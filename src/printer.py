from src.printer_models import PrinterModel


class Printer:
    def __init__(self, model: PrinterModel):
        self.model: PrinterModel = model
