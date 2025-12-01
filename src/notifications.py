import time
from pprint import pp
from typing import Any

import requests

from src.encryption import EncryptionHandler

RELAY_URL: str = (
    "https://europe-west1-octoapp-4e438.cloudfunctions.net/sendNotificationV2"
)


class NotificationHandler:
    _instance: NotificationHandler | None = None

    class Event:
        PRINTING: str = "printing"

    def __init__(self, data: dict[str, Any]):
        NotificationHandler._instance = self
        self.fcmToken = data["fcmToken"]
        self.fcmFallbackToken = data.get("fcmTokenFallback", None)
        self.instanceId = data["instanceId"]

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

    async def send_printing_notification(self):
        """
        Send a live printing notification to the app.
        """

    async def send_notification(self, event: Event, args: dict[str, str]):
        """
        Sends a notification to the app.

        Args:
            event (Event): The event type.
            args (dict[str, str]): The notification arguments.
        """

        # args = {
        #     "print_id": "8944ee389eb74db29f38c5b1152be975",  # A random 32-character string, globally unique
        #     "file_name": "ExamplePrint.gcode",
        #     "file_path": "/usb/ExamplePrint.gcode",
        #     "FileSizeKb": "1024",
        #     "FilamentUsageMm": "100",
        #     "FilamentWeightMg": "500",
        #     "Event": event,
        #     "time_remaining_sec": "300",
        #     "CurrentLayer": "14",
        #     "TotalLayers": "20",
        #     "progress_percent": "0",
        #     "duration_sec": "120",
        #     # "message": "Print completed successfully",
        # }

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

        notification_data = {
            "targets": [
                {
                    "fcmToken": "eDqwWjyhS06-UHWeeZYis3:APA91bEje10blwAZgET9wZP9y8L2wC1TljyIumBlCjzF6q4nXltESeXnlLsr7N0w_Y_wFTw_TlpcSdzamsyu0sG5qOyI14cZDWiWAol1gdozQHDUmND3qdg",
                    "fcmTokenFallback": None,
                    "instanceId": "bfb4b74d-291a-41fb-a55c-5e78aa8329fe",
                },
            ],
            "highPriority": True,
            "androidData": EncryptionHandler.get_instance().encrypt_notification(
                android_push_data
            ),
            "apnsData": None,
        }

        pp(notification_data)

        # Make the request
        response = requests.post(RELAY_URL, timeout=float(10), json=notification_data)
        print("Response headers:")
        pp(response.headers)
        print(response.text)
