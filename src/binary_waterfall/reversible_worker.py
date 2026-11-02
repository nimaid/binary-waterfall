"""Background worker for reversible video operations."""

from PyQt5.QtCore import QThread, pyqtSignal
from . import reversible_video


class ReversibleWorker(QThread):
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, action, source, destination, overwrite=False, parent=None):
        super().__init__(parent)
        self.action = action
        self.source = source
        self.destination = destination
        self.overwrite = overwrite

    def run(self):
        try:
            if self.action == "encode":
                reversible_video.encode(
                    self.source,
                    self.destination,
                    overwrite=self.overwrite,
                )
                self.succeeded.emit("Reversible video exported successfully!")
            elif self.action == "decode":
                reversible_video.decode(
                    self.source,
                    self.destination,
                    overwrite=self.overwrite,
                )
                self.succeeded.emit(
                    "Original file recovered and SHA-256 verified!"
                )
            else:
                raise ValueError("Unknown operation")
        except Exception as error:
            self.failed.emit(str(error))
