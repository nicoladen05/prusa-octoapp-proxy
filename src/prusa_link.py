import asyncio
from pprint import pp
from typing import Any, Final

import httpx


class PrusaLink:
    host: Final[str]
    username: Final[str]
    password: Final[str]
    client: httpx.AsyncClient | None
    auth: httpx.DigestAuth

    def __init__(self, host: str, username: str, password: str):
        """
        Initialize a PrusaLink instance.

        Args:
            host (str): The host address of the PrusaLink server.
            password (str): The password for the PrusaLink server.
        """

        self.host = host
        self.username = username
        self.password = password
        self.client = None
        self.auth = httpx.DigestAuth(self.username, self.password)

    async def connect(self):
        """
        Connect to the PrusaLink server.
        """

        self.client = httpx.AsyncClient(base_url=self.host)
        print("Connected to PrusaLink server.")

    async def disconnect(self):
        """
        Disconnect from the PrusaLink server.
        """

        if self.client:
            await self.client.aclose()
            self.client = None
            print("Disconnected from PrusaLink server.")

    async def _get(self, endpoint: str) -> dict[str, str] | None:
        """
        Send a GET request to the PrusaLink server.

        Args:
            endpoint (str): The endpoint to send the GET request to.

        Returns:
            dict[str, str]: The response from the PrusaLink server.
        """

        if not self.client:
            await self.connect()

        assert self.client is not None

        try:
            response = await self.client.get(endpoint, auth=self.auth)
            _ = response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error: {e}")
            return None

    async def get_version(self) -> dict[str, Any] | None:  # pyright: ignore[reportExplicitAny]
        """
        Get the version information from the PrusaLink server.

        Returns:
            dict[str, str]: The version information.
        """

        return await self._get("/api/version")

    async def get_info(self) -> dict[str, Any] | None:  # pyright: ignore[reportExplicitAny]
        """
        Get the information from the PrusaLink server.

        Returns:
            dict[str, str]: The information.
        """

        return await self._get("/api/v1/info")

    async def get_status(self) -> dict[str, Any] | None:  # pyright: ignore[reportExplicitAny]
        """
        Get the status from the PrusaLink server.

        Returns:
            dict[str, str]: The status.
        """

        return await self._get("/api/v1/status")

    async def get_job(self) -> dict[str, Any] | None:  # pyright: ignore[reportExplicitAny]
        """
        Get the job information from the PrusaLink server.

        Returns:
            dict[str, str]: The job information.
        """

        return await self._get("/api/v1/job")

    async def get_storage(self) -> dict[str, Any] | None:  # pyright: ignore[reportExplicitAny]
        """
        Get the storage information from the PrusaLink server.

        Returns:
            dict[str, str]: The storage information.
        """

        return await self._get("/api/v1/storage")

    async def get_files(self) -> dict[str, Any] | None:  # pyright: ignore[reportExplicitAny]
        """
        Get the files information from the PrusaLink server.

        Returns:
            dict[str, str]: The files information.
        """

        return await self._get("/api/v1/files/usb")


if __name__ == "__main__":
    prusa_link = PrusaLink("http://192.168.2.137", "maker", "izPjsV5TQJR4Eai")
    asyncio.run(prusa_link.connect())
    status = asyncio.run(prusa_link.get_status())
    assert status is not None
    pp(status)
