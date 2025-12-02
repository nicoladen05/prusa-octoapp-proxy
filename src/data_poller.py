import asyncio
from collections.abc import Coroutine
from enum import Enum
from typing import Any, Callable

from src.print_job import PrintJob
from src.printer_status import PrinterState, PrinterStatus
from src.prusa_link import PrusaLink


class DataPoller:
    """
    The DataPoller class is responsible for polling data from the PrusaLink API and notifying subscribers of changes.
    """

    _instance: DataPoller | None = None

    class Event(Enum):
        PRINTER_STATUS = 1
        PRINT_JOB = 2

    def __init__(self, link: PrusaLink):
        DataPoller._instance = self

        self.link: PrusaLink = link
        self._subscribers: dict[
            DataPoller.Event,
            set[Callable[[PrintJob | PrinterStatus], Coroutine[Any, Any, None]]],
        ] = {}
        self.current_print: PrintJob | None = None
        self.listen_task: asyncio.Task[None] | None = None
        self.previous_status: dict[str, Any] | None = None
        self.previous_job: dict[str, Any] | None = None

    async def start(self) -> None:
        self.listen_task = asyncio.create_task(self.listen(2))

    @classmethod
    def get_instance(cls) -> DataPoller:
        if cls._instance is None:
            raise ValueError("DataPoller instance not initialized")
        return cls._instance

    def subscribe(
        self,
        event: DataPoller.Event,
        callback: Callable[[PrintJob | PrinterStatus], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Subscribe to data updates for an event.

        Args:
            event (Event): The event to subscribe to.
            callback (Callable[[dict[str, Any]], Coroutine[Any, Any, None]]): The callback function to handle data updates.
        """
        self._subscribers.setdefault(event, set()).add(callback)

    def unsubscribe(
        self,
        event: DataPoller.Event,
        callback: Callable[[PrintJob | PrinterStatus], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Unsubscribe from data updates.

        Args:
            event (Event): The event to unsubscribe from.
            callback (Callable[[dict[str, Any]], Coroutine[Any, Any, None]]): The callback function to handle data updates.
        """
        self._subscribers.setdefault(event, set()).remove(callback)

    async def _notify_subscribers(
        self, event: DataPoller.Event, update: PrinterStatus | PrintJob
    ) -> None:
        for callback in self._subscribers.get(event, set()):
            await callback(update)

    async def listen(self, rate: float) -> None:
        """
        Listen for data updates.

        Args:
            rate (float): The rate at which to listen for data updates.
        """
        self.previous_status = None
        self.previous_job = None

        while True:
            if len(self._subscribers) == 0 or not await self.link.is_online():
                print("No subscribers or offline")
                await asyncio.sleep(rate * 5)
                continue

            # Check for status updates
            status: dict[str, Any] | None = await self.link.get_status()

            if status is not None and status != self.previous_status:
                printer: dict[str, int | str] = status["printer"]

                printer_status = PrinterStatus(
                    state=PrinterState(printer["state"]),
                    temp_bed=float(printer["temp_bed"]),
                    temp_nozzle=float(printer["temp_nozzle"]),
                    target_bed=float(printer["target_bed"]),
                    target_nozzle=float(printer["target_nozzle"]),
                    z_height=float(printer["axis_z"]),
                    flow=float(printer["flow"]),
                    speed=float(printer["speed"]),
                    fan_hotend_rpm=int(printer["fan_hotend"]),
                    fan_print_rpm=int(printer["fan_print"]),
                )

                await self._notify_subscribers(
                    DataPoller.Event.PRINTER_STATUS, printer_status
                )
                self.previous_status = status

            # Check for job updates
            job: dict[str, Any] | None = (
                await self.link.get_job()
                if (status is not None and status.get("job", None) is not None)
                else None
            )

            if job is not None and job != self.previous_job:
                if not (print_job := PrintJob.get(job["id"])):
                    print_job = PrintJob(
                        print_id=job["id"],
                        running=job["state"] == "PRINTING",
                        progress=float(job["progress"]),
                        time_remaining_seconds=int(job["time_remaining"]),
                        time_printing_seconds=int(job["time_printing"]),
                        display_name=job["file"]["display_name"],
                        path=job["file"]["path"],
                    )
                else:
                    print_job.update(
                        running=job["state"] == "PRINTING",
                        progress=float(job["progress"]),
                        time_remaining_seconds=int(job["time_remaining"]),
                        time_printing_seconds=int(job["time_printing"]),
                        display_name=job["file"]["display_name"],
                        path=job["file"]["path"],
                    )

                await self._notify_subscribers(DataPoller.Event.PRINT_JOB, print_job)
                self.previous_job = job

            await asyncio.sleep(rate)

    async def is_online(self) -> bool:
        """
        Check if the printer is online.

        Returns:
            bool: True if the printer is online, False otherwise.
        """

        return await self.link.is_online()

    def force_update(self) -> None:
        """
        Force an update of the printer status and job information.
        """

        self.previous_status = None
        self.previous_job = None
