import time
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from src.print_job import PrintJob
from src.printer_status import PrinterState, PrinterStatus

PAYLOAD_TEMPLATE = {
    "current": {
        "serverTime": time.time(),
        "state": {
            "text": "Operational",
            "flags": {
                "operational": True,
                "printing": False,
                "closedOrError": False,
                "error": False,
                "paused": False,
                "ready": False,
                "sdReady": True,
            },
        },
        "realTimeStats": {
            "toolhead": {
                "speedMmPerS": 0,
                "positionZ": 0,
            },
        },
        "currentZ": 0,
        "temps": [
            {
                "time": 0,
                "tool0": {
                    "actual": 0,
                    "target": 0,
                },
                "bed": {
                    "actual": 0,
                    "target": 0,
                },
            }
        ],
        "job": {
            "file": {
                "name": "",
                "display": "",
                "path": "",
                "type": "machinecode",
                "typePath": ["machinecode", "gcode"],
                "user": "prusa_admin",
            },
            "estimatedPrintTime": 0,
            "lastPrintTime": None,
            "user": "prusa_admin",
        },
        "progress": {
            "completion": 0,
            "filepos": 0,
            "printTime": 0,
            "printTimeLeft": 0,
            "printTimeOrigin": "linear",
        },
    }
}


class WebSocketHandler:
    _instance: WebSocketHandler | None = None

    def __init__(self):
        WebSocketHandler._instance = self
        self.websockets: set[WebSocket] = set()
        self.cached_payload: dict[str, Any] = PAYLOAD_TEMPLATE

    @classmethod
    def get_instance(cls) -> WebSocketHandler:
        if cls._instance is None:
            cls._instance = WebSocketHandler()
        return cls._instance

    async def register_ws(self, websocket: WebSocket) -> None:
        """
        Register a new WebSocket connection to receive updates.

        Args:
            websocket (WebSocket): The WebSocket connection to register.
        """

        await websocket.accept()

        # Send the connected payload of OctoPrint
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

        self.websockets.add(websocket)

        # Keep the connection alive
        try:
            while True:
                data = await websocket.receive_text()
                print(f"Received data: {data}")
        except WebSocketDisconnect:
            print("Client disconnected")
            await self.unregister_ws(websocket)
        except Exception as e:
            print(f"Error occurred: {e}")
            await self.unregister_ws(websocket)

    async def unregister_ws(self, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket (WebSocket): The WebSocket connection to unregister.
        """

        self.websockets.remove(websocket)

    async def handle_update(self, update_data: PrinterStatus | PrintJob) -> None:
        """
        Handle an update event.
        Subscriber for DataPoller.Event.PRINTER_STATUS

        Args:
            data (dict[str, Any]): The update data.
        """

        current_payload = self.cached_payload
        current_payload["current"]["serverTime"] = time.time()

        if isinstance(update_data, PrinterStatus):
            current_payload["current"]["state"] = {
                "text": "Operational",
                "flags": {
                    "operational": update_data.state != PrinterState.ERROR,
                    "printing": update_data.state == PrinterState.PRINTING
                    or update_data.state == PrinterState.PAUSED,
                    "closedOrError": update_data.state == PrinterState.ERROR,
                    "error": update_data.state == PrinterState.ERROR,
                    "paused": update_data.state == PrinterState.PAUSED,
                    "ready": update_data.state == PrinterState.READY,
                    "sdReady": True,
                },
            }
            current_payload["current"]["realTimeStats"] = {
                "toolhead": {
                    "speedMmPerS": update_data.speed,
                    "positionZ": update_data.z_height,
                },
            }
            current_payload["current"]["currentZ"] = update_data.z_height
            current_payload["current"]["temps"] = [
                {
                    "time": int(time.time()),
                    "tool0": {
                        "actual": update_data.temp_nozzle,
                        "target": update_data.target_nozzle,
                    },
                    "bed": {
                        "actual": update_data.temp_bed,
                        "target": update_data.target_bed,
                    },
                }
            ]

        else:
            current_payload["current"]["job"] = {
                "file": {
                    "name": update_data.display_name,
                    "display": update_data.display_name,
                    "path": update_data.path + "/" + update_data.display_name,
                    "type": "machinecode",
                    "typePath": ["machinecode", "gcode"],
                    "user": "prusa_admin",
                    "origin": "sdcard",
                },
                "estimatedPrintTime": update_data.time_printing_seconds
                + update_data.time_remaining_seconds,
                "lastPrintTime": None,
                "user": "prusa_admin",
            }
            current_payload["current"]["progress"] = {
                "completion": update_data.progress,
                "filepos": 500,
                "printTime": update_data.time_printing_seconds,
                "printTimeLeft": update_data.time_remaining_seconds,
                "printTimeOrigin": "linear",
            }

        self.cached_payload = current_payload

        for websocket in self.websockets:
            try:
                await websocket.send_json(current_payload)
            except Exception as e:  # Client disconnected
                print(f"Error: {e}")
