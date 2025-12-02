import time
from enum import Enum
from pprint import pp
from typing import Any

import requests

from src.encryption import EncryptionHandler
from src.print_job import PrintJob
from src.printer_status import PrinterStatus

RELAY_URL: str = (
    "https://europe-west1-octoapp-4e438.cloudfunctions.net/sendNotificationV2"
)


class NotificationHandler:
    _instance: NotificationHandler | None = None

    class Event(Enum):
        PRINTING = "printing"

    def __init__(self, data: dict[str, Any]):
        NotificationHandler._instance = self
        self.devices: set[dict[str, str | None]] = set({})

    def register(self, data: dict[str, Any]):
        """
        Register a device with the notification handler.

        Args:
            data (dict[str, Any]): The device data.
        """

        self.devices.add(
            {
                "fcmToken": data.get("fcmToken", None),
                "fcmFallbackToken": data.get("fcmTokenFallback", None),
                "instanceId": data.get("instanceId", None),
            }
        )

    def unregister(self, data: dict[str, Any]):
        """
        Unregister a device with the notification handler.

        Args:
            data (dict[str, Any]): The device data.
        """

        self.devices.remove(
            {
                "fcmToken": data.get("fcmToken", None),
                "fcmFallbackToken": data.get("fcmTokenFallback", None),
                "instanceId": data.get("instanceId", None),
            }
        )

    @classmethod
    def get_instance(cls) -> NotificationHandler:
        """
        Returns the instance of the NotificationHandler class, None if not initialized.
        """

        if cls._instance is None:
            raise ValueError("Notification Handler not initialized yet")
        return cls._instance

    @classmethod
    def is_registered(cls) -> bool:
        return cls._instance is not None

    async def send_printing_notification(self, print_job: PrintJob | PrinterStatus):
        """
        Send a live printing notification to the app.

        Args:
            print_job (PrintJob): The print job object.
        """

        if isinstance(print_job, PrinterStatus):
            raise ValueError("send_printing_notification was called without a PrintJob")

        args = {
            "print_id": print_job.notification_print_id,
            "file_name": print_job.display_name,
            "progress_percent": print_job.progress,
            "time_remaining_sec": print_job.time_remaining_seconds,
        }

        await self.send_notification(NotificationHandler.Event.PRINTING, args)

    async def send_notification(
        self, event: NotificationHandler.Event, args: dict[str, str | float | int]
    ):
        """
        Sends a notification to the app.

        Args:
            event (Event): The event type.
            args (dict[str, str]): The notification arguments.
        """

        android_push_data = {
            "type": event,
            "serverTime": int(time.time()),
            "serverTimePrecise": time.time(),
            "printId": args.get("print_id", None),
            "fileName": args.get("file_name", None),
            "progress": args.get("progress_percent", None),
            "timeLeft": args.get("time_remaining_sec", None),
            "message": args.get("message", None),
        }

        for device in self.devices:
            notification_data = {
                "targets": [
                    {
                        "fcmToken": device["fcmToken"],
                        "fcmTokenFallback": device["fcmToken"],
                        "instanceId": device["instanceId"],
                    },
                ],
                "highPriority": True,
                "androidData": EncryptionHandler.get_instance().encrypt_notification(
                    android_push_data
                ),
                "apnsData": None,
            }

            # Make the request
            response = requests.post(
                RELAY_URL, timeout=float(10), json=notification_data
            )
            print("Response headers:")
            pp(response.headers)
            print(response.text)
