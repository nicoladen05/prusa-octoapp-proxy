from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.data_poller import DataPoller
from src.data_routes import router as data_router
from src.octoprint_routes import router as octoprint_router
from src.prusa_link import PrusaLink
from src.websocket import WebSocketHandler

prusa_link = PrusaLink("http://192.168.2.137", "maker", "izPjsV5TQJR4Eai")
data_poller = DataPoller(prusa_link)


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_poller.subscribe(
        DataPoller.Event.PRINTER_STATUS, WebSocketHandler.get_instance().handle_update
    )
    data_poller.subscribe(
        DataPoller.Event.PRINT_JOB, WebSocketHandler.get_instance().handle_update
    )

    await data_poller.start()

    yield

    if data_poller.listen_task:
        _ = data_poller.listen_task.cancel()


def app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(octoprint_router)
    app.include_router(data_router)
    return app


if __name__ == "__main__":
    uvicorn.run(app(), host="0.0.0.0", port=8000)
