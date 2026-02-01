"""
Websocket server.
"""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from pytest_relay_ws.observer import AnyMessage

router = APIRouter()

src_clients: set[WebSocket] = set()  # pytest-source clients
snk_clients: set[WebSocket] = set()  # pytest-sink clients

logger = logging.getLogger("uvicorn")


def _try_parse(data: str, ws: WebSocket) -> None:
    # ignore multiple identification attempts
    if ws in src_clients or ws in snk_clients:
        return

    msg: Optional[AnyMessage] = None
    try:
        msg = AnyMessage.model_validate_json(data, strict=False)
    except ValidationError as _:  # pylint: disable=broad-except,bare-except
        pass

    if msg is not None:
        match msg.type:
            case "pytest-source":
                logger.info("client %s added as pytest-source", ws.client)
                src_clients.add(ws)
            case "pytest-sink":
                logger.info("client %s added as pytest-sink", ws.client)
                snk_clients.add(ws)
            case _:
                pass


async def _try_send(data: str, ws: WebSocket) -> None:
    try:
        await ws.send_text(data)
    except Exception:  # pylint: disable=broad-except
        # sending may fail if the client disconnected while we're trying to relay.
        pass


async def _try_relay(data: str, source: WebSocket) -> None:
    # relay source messages to sinks and vice versa.
    # snapshot as lists since the sets may be manipulated concurrently.
    dst = None
    if source in src_clients:
        dst = list(snk_clients)
    elif source in snk_clients:
        dst = list(src_clients)
    else:
        return

    if not dst:
        return

    logger.info(
        "relaying"
        f"\n  {json.dumps(json.loads(data), indent=2)}\n"
        f"  to {[ws.client for ws in dst]}"
    )

    coros = [_try_send(data, ws) for ws in dst]
    if coros:
        # run all relays concurrently, slow clients won't block others
        await asyncio.gather(*coros, return_exceptions=True)


async def publish(data: str, to_sink: bool = False, to_source: bool = False) -> None:
    """
    Publishes a message to sinks and sources.
    """
    dst = []
    if to_sink:
        dst.extend(list(snk_clients))
    if to_source:
        dst.extend(list(src_clients))

    if not dst:
        return

    logger.info(
        "publishing"
        f"\n  {json.dumps(json.loads(data), indent=2)}\n"
        f"  to {[ws.client for ws in dst]}"
    )

    coros = [_try_send(data, ws) for ws in dst]
    if coros:
        # run all relays concurrently, slow clients won't block others
        await asyncio.gather(*coros, return_exceptions=True)


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    Endpoint for websocket connections.
    """
    await websocket.accept()
    # acknowledge the connection
    await _try_send(AnyMessage(type="pytest-conn-ack").model_dump_json(), websocket)
    try:
        while True:
            data = await websocket.receive_text()
            _try_parse(data, websocket)
            await _try_relay(data, websocket)
    except WebSocketDisconnect:
        src_clients.discard(websocket)
        snk_clients.discard(websocket)


# keep the 'app' definition at the end since all included routes must exist when defining the app
app = FastAPI(title="pytest-relay-run-ws")
app.include_router(router)
