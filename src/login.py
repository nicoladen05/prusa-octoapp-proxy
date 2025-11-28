import asyncio
import time
from typing import cast

from fastapi import Request, Response, WebSocket
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


@router.get("/api/currentuser")
async def get_current_user():
    return {
        "name": "prusa_admin",
        "groups": ["admins", "users"],
        "permissions": [
            "ADMIN",
            "STATUS",
            "CONNECTION",
            "WEBCAM",
            "SYSTEM",
            "FILES_LIST",
            "FILES_UPLOAD",
            "FILES_DOWNLOAD",
            "FILES_DELETE",
            "FILES_SELECT",
            "PRINT",
            "GCODE_VIEWER",
            "MONITOR_TERMINAL",
            "CONTROL",
            "SLICE",
            "TIMELAPSE_LIST",
            "TIMELAPSE_DOWNLOAD",
            "TIMELAPSE_DELETE",
            "TIMELAPSE_MANAGE_UNRENDERED",
            "TIMELAPSE_ADMIN",
            "SETTINGS_READ",
            "SETTINGS",
            "PLUGIN_ACHIEVEMENTS_VIEW",
            "PLUGIN_ACHIEVEMENTS_RESET",
            "PLUGIN_ACTION_COMMAND_NOTIFICATION_SHOW",
            "PLUGIN_ACTION_COMMAND_NOTIFICATION_CLEAR",
            "PLUGIN_ACTION_COMMAND_PROMPT_INTERACT",
            "PLUGIN_ANNOUNCEMENTS_READ",
            "PLUGIN_ANNOUNCEMENTS_MANAGE",
            "PLUGIN_APPKEYS_ADMIN",
            "PLUGIN_APPKEYS_GRANT",
            "PLUGIN_BACKUP_CREATE",
            "PLUGIN_FILE_CHECK_RUN",
            "PLUGIN_FIRMWARE_CHECK_DISPLAY",
            "PLUGIN_HEALTH_CHECK_CHECK",
            "PLUGIN_LOGGING_MANAGE",
            "PLUGIN_PLUGINMANAGER_LIST",
            "PLUGIN_PLUGINMANAGER_MANAGE",
            "PLUGIN_PLUGINMANAGER_INSTALL",
            "PLUGIN_SOFTWAREUPDATE_CHECK",
            "PLUGIN_SOFTWAREUPDATE_UPDATE",
            "PLUGIN_SOFTWAREUPDATE_CONFIGURE",
        ],
    }


class LoginRequest(BaseModel):
    passive: bool = False
    user: str | None = None
    password: str | None = Field(None, alias="pass")
    remember: bool = False


@router.post("/api/login")
async def login(_login_data: LoginRequest, _response: Response):
    login_response: dict[str, bool | str] = {
        "_is_external_client": False,
        "session": "session12345",
    }

    return login_response


@router.get("/sockjs/info")
async def sockjs_info():
    return {
        "websocket": True,
        "origins": ["*:*"],
        "cookie_needed": False,
        "entropy": 424242,
    }


async def handle_socket(websocket: WebSocket):
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
            # THE FIX: Added "serverTime" to "current" object
            current_payload = {
                "current": {
                    "serverTime": time.time(),  # <--- THIS WAS MISSING AND CAUSED THE CRASH
                    "state": {
                        "text": "Operational",
                        "flags": {
                            "operational": True,
                            "printing": False,
                            "closedOrError": False,
                            "error": False,
                            "paused": False,
                            "ready": True,
                            "sdReady": True,
                        },
                    },
                    "job": {
                        "file": {
                            "name": None,
                            "size": None,
                            "origin": None,
                            "date": None,
                        },
                        "estimatedPrintTime": 100,
                        "lastPrintTime": None,
                        "user": "prusa_admin",
                    },
                    "progress": {
                        "completion": None,
                        "filepos": None,
                        "printTime": None,
                        "printTimeLeft": None,
                        "printTimeOrigin": None,
                    },
                    "currentZ": 0.0,
                    "offsets": {},
                    "resends": {"count": 0, "transmitted": 0, "ratio": 0},
                    "temps": [
                        {
                            "time": int(time.time()),
                            "tool0": {"actual": 215.0, "target": 215.0},
                            "bed": {"actual": 60.0, "target": 60.0},
                        }
                    ],
                    "logs": [],
                }
            }

            await websocket.send_json(current_payload)
            await asyncio.sleep(2.0)
    except Exception as e:
        print(f"Socket Disconnected: {e}")


@router.websocket("/sockjs/{server_id}/{session_id}/websocket")
async def sockjs_session(websocket: WebSocket, _server_id: str, _session_id: str):
    await handle_socket(websocket)


@router.websocket("/sockjs/websocket")
async def sockjs_raw(websocket: WebSocket):
    await handle_socket(websocket)


@router.get("/api/version")
async def get_version():
    return {"api": "0.1", "server": "1.11.4", "text": "OctoPrint 1.11.4"}


@router.get("/api/connection")
async def get_connection():
    return {
        "current": {
            "state": "Operational",
            "port": "/dev/ttyUSB0",
            "baudrate": 115200,
            "printerProfile": "_default",
        },
        "options": {
            "ports": ["/dev/ttyUSB0"],
            "baudrates": [115200],
            "printerProfiles": [{"id": "_default", "name": "Prusa MK3/4"}],
        },
    }


@router.post("/api/connection")
async def post_connection(request: Request):
    data: dict[str, str] = cast(dict[str, str], await request.json())
    print(f" >>> OCTOAPP SENT COMMAND: {data}")

    if data.get("command") == "disconnect":
        return Response(status_code=204)

    return Response(status_code=204)


@router.get("/api/settings")
async def get_settings():
    return {
        "api": {"allowCrossOrigin": False, "key": None},
        "appearance": {"name": "Prusa Proxy"},
        "feature": {
            "gcodeViewer": True,
            "temperatureGraph": True,
            "modelSizeDetection": False,
        },
        "folder": {
            "uploads": "/home/pi/.octoprint/uploads",
            "watched": "/home/pi/.octoprint/watched",
            "logs": "/home/pi/.octoprint/logs",
        },
    }


@router.get("/api/printerprofiles")
async def get_printerprofiles():
    return {
        "profiles": {
            "_default": {
                "id": "_default",
                "name": "Prusa MK3/4",
                "model": "MK3S",
                "default": True,
                "current": True,
                "heatedBed": True,
                "axes": {
                    "x": {"speed": 6000, "inverted": False},
                    "y": {"speed": 6000, "inverted": False},
                    "z": {"speed": 200, "inverted": False},
                    "e": {"speed": 300, "inverted": False},
                },
                "volume": {
                    "formFactor": "rectangular",
                    "origin": "lowerleft",
                    "width": 250.0,
                    "depth": 210.0,
                    "height": 210.0,
                    "custom_box": False,
                },
            }
        }
    }


@router.get("/api/system/info")
async def system_info() -> dict[
    str,
    dict[str, list[None] | dict[str, int] | dict[str, str]]
    | dict[str, dict[str, list[None]]],
]:
    return {
        "system": {
            "actions": [],
            "hardware": {"cores": 4, "freq": 1500, "ram": 999999},
            "os": {"type": "linux", "version": "Simulated"},
            "python": {"version": "3.9.0", "pip": "20.0"},
        },
        "systeminfo": {"system": {"actions": []}},
    }


@router.get("/api/system/commands")
async def system_commands() -> list[None]:
    return []


@router.get("/api/printer")
async def printer_status():
    return {
        "temperature": {
            "tool0": {"actual": 215.0, "target": 215.0, "offset": 0},
            "bed": {"actual": 60.0, "target": 60.0, "offset": 0},
        },
        "sd": {"ready": True},
        "state": {
            "text": "Operational",
            "flags": {
                "operational": True,
                "printing": False,
                "ready": True,
                "closedOrError": False,
                "error": False,
                "paused": False,
            },
        },
    }


@router.get("/plugin/pluginmanager/plugins/versions")
async def plugin_versions() -> dict[None, None]:
    return {}
