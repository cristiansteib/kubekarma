"""This module contains the principal class to collect the results of the tests.
"""
import asyncio
import threading
from typing import Optional

from fastapi import FastAPI, Response, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pydantic import BaseModel


import logging


import uvicorn
from uvicorn.config import Config

from kubekarma.controlleroperator.core.controllerengine import ControllerEngine

app = FastAPI()

logger = logging.getLogger(__name__)

the_controller_engine: Optional[ControllerEngine] = None


# this model should be symmetric with shared.genericcrd.TestCaseResultItem
class TestResultsModel(BaseModel):
    name: str
    status: str
    executionTime: str
    lastExecutionTime: str  # time in timestamp format


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logger.error(f"{request}: {exc_str}")
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(
        content=content,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


@app.get("/healthz")
def healthz(response: Response,  include_in_schema=False):
    #
    response.status_code = status.HTTP_200_OK
    if not the_controller_engine or not the_controller_engine.is_healthy():
        response.status_code = status.HTTP_425_TOO_EARLY
        return {"status": "not ok"}
    return {"status": "ok"}


class ThreadedUvicorn:
    """A wrapper to run uvicorn in a thread.

    Why? because I need to control the lifecycle of the http server
    to stop it properly when the operator is stopped.
    """

    def __init__(self, config: Config):
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(daemon=True, target=self.server.run)
        self.is_running = False

    def start(self):
        self.thread.start()
        asyncio.run(self.wait_for_started())
        self.is_running = True

    async def wait_for_started(self):
        while not self.server.started:
            await asyncio.sleep(0.01)

    def stop(self):
        if self.thread.is_alive():
            self.server.should_exit = True
            while self.thread.is_alive():
                continue


def get_threaded_server(
        http_host: str = "127.0.0.1",
        http_port: int = 8000,
        controller_engine: Optional[ControllerEngine]=None
) -> ThreadedUvicorn:
    """Get a threaded http server to receive the results of the tests."""
    global the_controller_engine
    the_controller_engine = controller_engine or ControllerEngine()
    config = Config(app=app, host=http_host, port=http_port)
    server = ThreadedUvicorn(config)
    return server


def start_server(http_host: str = "127.0.0.1", http_port: int = 8000):
    import uvicorn
    uvicorn.run(
        app=app,
        host=http_host,
        port=http_port
    )


if __name__ == '__main__':
    start_server()
