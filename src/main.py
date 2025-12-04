from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from data_poller import DataPoller
from data_routes import router as data_router
from notifications import NotificationHandler
from octoprint_routes import router as octoprint_router
from prusa_link import PrusaLink
from websocket import WebSocketHandler


def main():
    uvicorn.run(app(), host="0.0.0.0", port=8000)


@asynccontextmanager
async def lifespan(app: FastAPI):
    prusa_link = PrusaLink("http://192.168.2.137", "maker", "izPjsV5TQJR4Eai")
    data_poller = DataPoller(prusa_link)

    data_poller.subscribe(
        DataPoller.Event.PRINTER_STATUS, WebSocketHandler.get_instance().handle_update
    )
    data_poller.subscribe(
        DataPoller.Event.PRINT_JOB, WebSocketHandler.get_instance().handle_update
    )
    data_poller.subscribe(
        DataPoller.Event.PRINT_JOB,
        NotificationHandler.get_instance().send_printing_notification,
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
    main()
