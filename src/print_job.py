import string
from random import choices


class PrintJob:
    _print_jobs: set[PrintJob] = set()

    def __init__(
        self,
        print_id: int,
        running: bool,
        progress: float,
        time_remaining_seconds: int,
        time_printing_seconds: int,
        display_name: str,
        path: str,
    ):
        self.print_id: int = print_id
        self.notification_print_id: str = "".join(
            choices(string.ascii_lowercase + string.digits, k=32)
        )
        self.running: bool = False
        self.progress: float = 0.0
        self.time_remaining_seconds: int = 0
        self.time_printing_seconds: int = 0
        self.display_name: str = ""
        self.path: str = ""

        PrintJob._print_jobs.add(self)

    @staticmethod
    def get(id: str) -> PrintJob | None:
        """
        Returns a PrintJob object with the given ID, or None if not found.

        Args:
            id (str): The ID of the PrintJob to retrieve.

        Returns:
            PrintJob | None: The PrintJob object with the given ID, or None if not found.
        """

        for job in PrintJob._print_jobs:
            if job.print_id == id:
                return job
        else:
            return None

    def update(
        self,
        running: bool,
        progress: float,
        time_remaining_seconds: int,
        time_printing_seconds: int,
        display_name: str,
        path: str,
    ):
        """
        Updates the PrintJob object with the given values.

        Args:
            running (bool): Whether the print job is currently running.
            progress (float): The progress of the print job as a percentage.
            time_remaining_seconds (int): The estimated time remaining for the print job in seconds.
            time_printing_seconds (int): The total time spent printing the job in seconds.
            display_name (str): The display name of the print job.
            path (str): The path to the print job file.
        """
        self.running = running
        self.progress = progress
        self.time_remaining_seconds = time_remaining_seconds
        self.time_printing_seconds = time_printing_seconds
        self.display_name = display_name
        self.path = path
