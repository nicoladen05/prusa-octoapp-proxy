from pprint import pp
from typing import Any, cast

from fastapi import Request, Response
from fastapi.routing import APIRouter
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from src.data_poller import DataPoller
from src.encryption import EncryptionHandler
from src.notifications import NotificationHandler

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


@router.get("/api/version")
async def get_version():
    return {"api": "0.1", "server": "1.11.4", "text": "OctoPrint 1.11.4"}


@router.get("/api/connection")
async def get_connection():
    if await DataPoller.get_instance().is_online():
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
    else:
        print("Printer is offline")
        return {}


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
        "appearance": {
            "name": "Prusa CORE One"
        },  # TODO: Display the actual name of the printer
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
        "plugins": {
            "octoapp": {
                "version": "3.0.3",
                "encryptionKey": EncryptionHandler.get_instance().get_key(),
            }
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
async def system_commands() -> dict[None, None]:
    return {}


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
async def plugin_versions() -> dict[str, str | None]:
    return {
        "octoapp": "3.0.3",
    }


@router.post("/api/plugin/octoapp")
async def octoapp_plugin(request: Request):
    payload: dict[str, Any] = await request.json()
    command = payload.get("command")

    match command:
        case "getPrinterFirmware":
            print("OctoApp requested printer firmware")
            return {
                "name": "Marlin",
                "version": "2.1.2",
                "text": "Marlin firmware version 2.1.2",
            }

        case "registerForNotifications":
            print("OctoApp registered for notifications")
            _ = NotificationHandler(payload)
            return {"result": "ok"}

        case _:
            print(f"Unknown command from OctoApp: {command}")
            pp(payload)
            return JSONResponse(status_code=400, content={"error": "Unknown command"})
