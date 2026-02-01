"""
.
"""

import argparse
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from pytest_relay_run.api.app import app as app_api
from pytest_relay_run.api.job import inject_async_loop
from pytest_relay_run.ws.app import app as app_ws

# import importlib
# version = importlib.metadata.version("pytest_relay_run")


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """
    https://fastapi.tiangolo.com/advanced/events/
    """
    inject_async_loop(asyncio.get_running_loop())
    yield


app = FastAPI(lifespan=_lifespan)
# mount REST API at /api
app.mount("/api", app_api)
# mount WebSocket server at root
app.mount("/", app_ws)


def run() -> None:
    """
    Entry point for CLI.
    """
    parser = argparse.ArgumentParser(description="pytest-relay-run server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="application host")
    parser.add_argument("--port", type=int, default=8000, help="application port")

    args = parser.parse_args()
    uvicorn.run("pytest_relay_run.main:app", host=args.host, port=args.port)


if __name__ == "__main__":
    run()
