import socket
from typing import cast

from zeroconf import ServiceInfo, Zeroconf

PRINTER_NAME = "Prusa CORE One"


class NotificationHandler:
    def register_mdns(self):
        # Get the local ip
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_ip: str = "127.0.0.1"

        try:
            s.connect(("10.255.255.255", 1))
            local_ip: str = cast(str, s.getsockname()[0])
        except Exception as _:
            print("Error occurred while getting local IP")
        finally:
            s.close()

        print(f"Broadcasting to {local_ip}:8000")

        description = {
            "path": "/",
            "version": "1.9.0",
            "api": "0.1",
            "uuid": "12345678-1234-1234-1234-123456789012",
        }

        info = ServiceInfo(
            "_octoprint._tcp.local.",
            f"{PRINTER_NAME}._octoprint._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=8000,
            properties=description,
            server=f"{PRINTER_NAME.replace(' ', '_')}.local.",
        )

        zeroconf = Zeroconf()
        zeroconf.register_service(info)


if __name__ == "__main__":
    NotificationHandler().register_mdns()
