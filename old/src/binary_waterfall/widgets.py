import math
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QAbstractButton, QSlider, QStyle
from PyQt5.QtGui import QPainter

from . import constants

# Custom image-based button
#   Allows for very fancy custom buttons
class ImageButton(QAbstractButton):
    def __init__(self,
                 pixmap,
                 pixmap_hover,
                 pixmap_pressed,
                 scale=1.0,
                 parent=None
                 ):
        super(ImageButton, self).__init__(parent)
        self.scale = scale
        self.height = None
        self.width = None
        self.pixmap_pressed = None
        self.pixmap_hover = None
        self.pixmap = None

        self.change_pixmaps(
            pixmap=pixmap,
            pixmap_hover=pixmap_hover,
            pixmap_pressed=pixmap_pressed
        )

        self.pressed.connect(self.update)
        self.released.connect(self.update)

    def change_pixmaps(self,
                       pixmap,
                       pixmap_hover,
                       pixmap_pressed
                       ):
        self.pixmap = pixmap
        self.pixmap_hover = pixmap_hover
        self.pixmap_pressed = pixmap_pressed

        self.width = round(self.pixmap.width() * self.scale)
        self.height = round(self.pixmap.height() * self.scale)

        self.update()

    def paintEvent(self, event):
        if self.isDown():
            pix = self.pixmap_pressed
        elif self.underMouse():
            pix = self.pixmap_hover
        else:
            pix = self.pixmap

        painter = QPainter(self)
        painter.drawPixmap(event.rect(), pix)

    def enterEvent(self, event):
        self.update()

    def leaveEvent(self, event):
        self.update()

    def sizeHint(self):
        return QSize(self.width, self.height)


# Custom seekbar class
#   A customized slider
class SeekBar(QSlider):
    def __init__(self,
                 position_changed_function=None,
                 parent=None
                 ):
        super(SeekBar, self).__init__(parent)

        self.position_changed_function = position_changed_function

    def set_position_changed_function(self, position_changed_function):
        self.position_changed_function = position_changed_function

    def set_position_if_set(self, value):
        if self.position_changed_function is None:
            self.setValue(value)
        else:
            self.position_changed_function(value)

    def mousePressEvent(self, event):
        value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
        self.set_position_if_set(value)

    def mouseMoveEvent(self, event):
        value = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), event.x(), self.width())
        self.set_position_if_set(value)
