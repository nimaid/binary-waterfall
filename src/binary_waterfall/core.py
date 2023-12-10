import os
import sys
from enum import Enum
import re
import shutil
import math
import wave
import pydub
from moviepy.editor import ImageSequenceClip, AudioFileClip
import time
import tempfile
import webbrowser
from proglog import ProgressBarLogger
from PIL import Image, ImageOps
from PyQt5.QtCore import Qt, QUrl, QTimer, QSize
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton,
    QFileDialog, QAction,
    QDialog, QDialogButtonBox, QComboBox, QLineEdit, QCheckBox,
    QSpinBox, QDoubleSpinBox,
    QMessageBox,
    QAbstractButton,
    QSlider, QDial,
    QStyle,
    QProgressDialog
)
from PyQt5.QtGui import (
    QImage, QPixmap, QIcon,
    QPainter
)

from . import constants, helpers














# Main window class
#   Handles variables related to the main window.
#   Any actual program functionality or additional dialogs are
#   handled using different classes
class MainWindow:
    def __init__(self, qt_args):
        self.app = QApplication(qt_args)
        self.window = MyQMainWindow()

    def run(self):
        self.window.show()
        self.app.exec()


def main(args):
    main_window = MainWindow(args)
    main_window.run()


def run():
    main(sys.argv)
