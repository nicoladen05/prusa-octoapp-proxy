import asyncio

from fastapi import APIRouter, Request, WebSocket

from src.data_poller import DataPoller
from src.notifications import NotificationHandler
from src.websocket import WebSocketHandler

router = APIRouter()


@router.get("/sockjs/info")
async def sockjs_info():
    return {
        "websocket": True,
        "origins": ["*:*"],
        "cookie_needed": False,
        "entropy": 424242,
    }


@router.websocket("/sockjs/{server_id}/{session_id}/websocket")
async def sockjs_session(websocket: WebSocket, _server_id: str, _session_id: str):
    await WebSocketHandler.get_instance().register_ws(websocket)


@router.websocket("/sockjs/websocket")
async def sockjs_raw(websocket: WebSocket):
    await WebSocketHandler.get_instance().register_ws(websocket)


@router.post("/api/printer/command")
async def printer_command(request: Request):
    await asyncio.sleep(3)
    await NotificationHandler.get_instance().send_notification()
