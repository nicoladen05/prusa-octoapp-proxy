import asyncio
import time

from fastapi import APIRouter, WebSocket

from src.prusa_link import PrusaLink

router = APIRouter()
prusa_link = PrusaLink("http://192.168.2.137", "maker", "izPjsV5TQJR4Eai")


async def handle_socket(websocket: WebSocket):
    """
    Handle WebSocket connection.
    """

    await websocket.accept()
    print(" > WebSocket Joined!")

    # 1. Handshake
    await websocket.send_json(
        {
            "connected": {
                "version": "1.9.0",
                "display_version": "1.9.0",
                "branch": "master",
                "module": "OctoPrint",
                "apikey": "dummy",
                "config_hash": "dummy",
            }
        }
    )

    # 2. History
    await websocket.send_json({"history": {"temps": [], "logs": []}})

    # 3. Loop
    try:
        while True:
            status = await prusa_link.get_status()

            if not status:
                continue

            assert status is not None

            info = await prusa_link.get_info()

            if not info:
                continue

            assert info is not None

            printing = status["printer"]["state"] == "PRINTING"
            paused = status["printer"]["state"] == "PAUSED"
            error = status["printer"]["state"] == "ERROR"
            ready = status["printer"]["state"] == "READY"
            idle = status["printer"]["state"] == "IDLE"

            if printing or paused:
                current_payload = {
                    "current": {
                        "serverTime": time.time(),
                        "state": {
                            "text": "Operational",
                            "flags": {
                                "operational": True,
                                "printing": printing,
                                "closedOrError": False,
                                "error": error,
                                "paused": paused,
                                "ready": printing or error or idle,
                                "sdReady": True,
                            },
                        },
                        "job": {
                            "file": {
                                "name": "Test",
                                "display": "something.gcode",
                                "path": "/path/to/file",
                                "type": "machinecode",
                                "typePath": ["machinecode", "gcode"],
                                "user": "prusa_admin",
                            },
                            "estimatedPrintTime": 100,
                            "lastPrintTime": None,
                            "user": "prusa_admin",
                        },
                        "progress": {
                            "completion": status["job"]["progress"],
                            "filepos": None,
                            "printTime": status["job"]["time_printing"],
                            "printTimeLeft": status["job"]["time_remaining"],
                            "printTimeOrigin": "linear",
                        },
                        "realTimeStats": {
                            "toolhead": {
                                "speedMmPerS": status["printer"]["speed"],
                                "positionZ": status["printer"]["axis_z"],
                            },
                        },
                        "currentZ": 0.0,
                        "offsets": {},
                        "resends": {"count": 0, "transmitted": 0, "ratio": 0},
                        "temps": [
                            {
                                "time": int(time.time()),
                                "tool0": {
                                    "actual": status["printer"]["temp_nozzle"],
                                    "target": status["printer"]["target_nozzle"],
                                },
                                "bed": {
                                    "actual": status["printer"]["temp_bed"],
                                    "target": status["printer"]["target_bed"],
                                },
                            }
                        ],
                        "logs": [],
                    }
                }
            else:
                current_payload = {
                    "current": {
                        "serverTime": time.time(),
                        "state": {
                            "text": "Operational",
                            "flags": {
                                "operational": True,
                                "printing": printing,
                                "closedOrError": False,
                                "error": error,
                                "paused": paused,
                                "ready": printing or error or idle,
                                "sdReady": True,
                            },
                        },
                        "temps": [
                            {
                                "time": int(time.time()),
                                "tool0": {
                                    "actual": status["printer"]["temp_nozzle"],
                                    "target": status["printer"]["target_nozzle"],
                                },
                                "bed": {
                                    "actual": status["printer"]["temp_bed"],
                                    "target": status["printer"]["target_bed"],
                                },
                            }
                        ],
                        "logs": [],
                    }
                }

            await websocket.send_json(current_payload)
            await asyncio.sleep(2.0)
    except Exception as e:
        print(f"Socket Disconnected: {e}")


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
    await handle_socket(websocket)


@router.websocket("/sockjs/websocket")
async def sockjs_raw(websocket: WebSocket):
    await handle_socket(websocket)
