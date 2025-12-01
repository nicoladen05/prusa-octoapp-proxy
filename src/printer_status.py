from enum import Enum


class PrinterState(Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    PRINTING = "PRINTING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    ATTENTION = "ATTENTION"
    READY = "READY"


class PrinterStatus:
    def __init__(
        self,
        state: PrinterState,
        temp_bed: float,
        target_bed: float,
        temp_nozzle: float,
        target_nozzle: float,
        z_height: float,
        flow: float,
        speed: float,
        fan_hotend_rpm: int,
        fan_print_rpm: int,
    ):
        self.state: PrinterState = state
        self.temp_bed: float = temp_bed
        self.target_bed: float = target_bed
        self.temp_nozzle: float = temp_nozzle
        self.target_nozzle: float = target_nozzle
        self.z_height: float = z_height
        self.flow: float = flow
        self.speed: float = speed
        self.fan_hotend_rpm: int = fan_hotend_rpm
        self.fan_print_rpm: int = fan_print_rpm
