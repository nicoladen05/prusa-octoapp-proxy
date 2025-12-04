from fastapi import APIRouter, WebSocket

from data_poller import DataPoller
from websocket import WebSocketHandler

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
    DataPoller.get_instance().force_update()
    await WebSocketHandler.get_instance().register_ws(websocket)


@router.websocket("/sockjs/websocket")
async def sockjs_raw(websocket: WebSocket):
    DataPoller.get_instance().force_update()
    await WebSocketHandler.get_instance().register_ws(websocket)
