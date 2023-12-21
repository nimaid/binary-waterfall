import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor

from . import window, constants

# TODO: Allow specifying custom audio and video bitrates (see OBS settings for ideas)
# TODO: Add unit testing (https://realpython.com/python-testing/)
# TODO: Add documentation (https://realpython.com/python-doctest/)

# Main window class
#   Handles variables related to the main window.
#   Any actual program functionality or additional dialogs are
#   handled using different classes
class MainWindow:
    def __init__(self, qt_args):
        # Apply dark mode on Windows systems
        if constants.PLATFORM == constants.PlatformCode.WINDOWS:
            os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=1"

        # Make main objects
        self.app = QApplication(qt_args)
        self.window = window.MyQMainWindow()

        # Setup colors
        self.app.setStyle("fusion")
        self.palette = QPalette()
        self.palette.setColor(QPalette.Window, QColor(constants.COLORS["background"]))
        self.palette.setColor(QPalette.WindowText, QColor(constants.COLORS["text"]))
        self.palette.setColor(QPalette.Base, QColor(constants.COLORS["foreground"]))
        self.palette.setColor(QPalette.AlternateBase, QColor(constants.COLORS["foreground"]))
        self.palette.setColor(QPalette.ToolTipBase, Qt.black)
        self.palette.setColor(QPalette.ToolTipText, Qt.white)
        self.palette.setColor(QPalette.Text, Qt.white)
        self.palette.setColor(QPalette.Button, QColor(constants.COLORS["foreground"]))
        self.palette.setColor(QPalette.ButtonText, QColor(constants.COLORS["button_text"]))
        self.palette.setColor(QPalette.BrightText, Qt.red)
        self.palette.setColor(QPalette.Link, QColor(constants.COLORS["link"]))
        self.palette.setColor(QPalette.Highlight, QColor(constants.COLORS["link"]))
        self.palette.setColor(QPalette.HighlightedText, Qt.black)

        self.palette.setColorGroup(
            QPalette.Disabled,
            self.palette.windowText(),
            QColor(constants.COLORS["disabled"]),
            self.palette.light(),
            self.palette.dark(),
            self.palette.mid(),
            QColor(constants.COLORS["disabled_text"]),
            self.palette.brightText(),
            QColor(constants.COLORS["disabled"]),
            self.palette.window()
        )

        self.app.setPalette(self.palette)

    def run(self):
        self.window.show()
        self.app.exec()


def main(args):
    if constants.HAS_SPLASH:
        import pyi_splash
        pyi_splash.close()

    main_window = MainWindow(args)
    main_window.run()


def run():
    main(sys.argv)
