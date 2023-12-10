
import sys
from PyQt5.QtWidgets import QApplication

from . import window

# Main window class
#   Handles variables related to the main window.
#   Any actual program functionality or additional dialogs are
#   handled using different classes
class MainWindow:
    def __init__(self, qt_args):
        self.app = QApplication(qt_args)
        self.window = window.MyQMainWindow()

    def run(self):
        self.window.show()
        self.app.exec()


def main(args):
    main_window = MainWindow(args)
    main_window.run()


def run():
    main(sys.argv)
