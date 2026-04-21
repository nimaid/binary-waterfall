import os
import webbrowser
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout, QLabel, QPushButton, QDialog, QDialogButtonBox, QComboBox, QLineEdit, QCheckBox, QSpinBox,
    QDoubleSpinBox, QMessageBox
)
from PyQt5.QtGui import QPixmap, QIcon

from . import constants


# Audio settings input window
#   User interface to set the audio settings (for computation)
class AudioSettings(QDialog):
    def __init__(self,
                 num_channels,
                 sample_bytes,
                 sample_rate,
                 volume,
                 parent=None
                 ):
        super().__init__(parent=parent)
        self.setWindowTitle("Audio Settings")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.num_channels = num_channels
        self.sample_bytes = sample_bytes
        self.sample_rate = sample_rate
        self.volume = volume

        self.channels_label = QLabel("Channels:")
        self.channels_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.channels_entry = QComboBox()
        self.channels_entry.addItems(["1 (mono)", "2 (stereo)"])
        if self.num_channels == 1:
            self.channels_entry.setCurrentIndex(0)
        elif self.num_channels == 2:
            self.channels_entry.setCurrentIndex(1)
        self.channels_entry.currentIndexChanged.connect(self.channel_entry_changed)

        self.sample_size_label = QLabel("Sample Size:")
        self.sample_size_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.sample_size_entry = QComboBox()
        self.sample_size_entry.addItems(["8-bit", "16-bit", "24-bit", "32-bit"])
        if self.sample_bytes == 1:
            self.sample_size_entry.setCurrentIndex(0)
        elif self.sample_bytes == 2:
            self.sample_size_entry.setCurrentIndex(1)
        elif self.sample_bytes == 3:
            self.sample_size_entry.setCurrentIndex(2)
        elif self.sample_bytes == 4:
            self.sample_size_entry.setCurrentIndex(3)
        self.sample_size_entry.currentIndexChanged.connect(self.sample_size_entry_changed)

        self.sample_rate_label = QLabel("Sample Rate:")
        self.sample_rate_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.sample_rate_entry = QSpinBox()
        self.sample_rate_entry.setMinimum(1)
        self.sample_rate_entry.setMaximum(192000)
        self.sample_rate_entry.setSingleStep(1000)
        self.sample_rate_entry.setSuffix("Hz")
        self.sample_rate_entry.setValue(self.sample_rate)
        self.sample_rate_entry.valueChanged.connect(self.sample_rate_entry_changed)

        self.volume_label = QLabel("File Volume:")
        self.volume_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.volume_entry = QSpinBox()
        self.volume_entry.setMinimum(0)
        self.volume_entry.setMaximum(100)
        self.volume_entry.setSingleStep(5)
        self.volume_entry.setSuffix("%")
        self.volume_entry.setValue(self.volume)
        self.volume_entry.valueChanged.connect(self.volume_entry_changed)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirm_buttons.accepted.connect(self.accept)
        self.confirm_buttons.rejected.connect(self.reject)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.channels_label, 0, 0)
        self.main_layout.addWidget(self.channels_entry, 0, 1)
        self.main_layout.addWidget(self.sample_size_label, 1, 0)
        self.main_layout.addWidget(self.sample_size_entry, 1, 1)
        self.main_layout.addWidget(self.sample_rate_label, 2, 0)
        self.main_layout.addWidget(self.sample_rate_entry, 2, 1)
        self.main_layout.addWidget(self.volume_label, 3, 0)
        self.main_layout.addWidget(self.volume_entry, 3, 1)
        self.main_layout.addWidget(self.confirm_buttons, 4, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def get_audio_settings(self):
        result = dict()
        result["num_channels"] = self.num_channels
        result["sample_bytes"] = self.sample_bytes
        result["sample_rate"] = self.sample_rate
        result["volume"] = self.volume

        return result

    def channel_entry_changed(self, idx):
        if idx == 0:
            self.num_channels = 1
        elif idx == 1:
            self.num_channels = 2

    def sample_size_entry_changed(self, idx):
        if idx == 0:
            self.sample_bytes = 1
        elif idx == 1:
            self.sample_bytes = 2
        elif idx == 2:
            self.sample_bytes = 3
        elif idx == 3:
            self.sample_bytes = 4

    def sample_rate_entry_changed(self, value):
        self.sample_rate = value

    def volume_entry_changed(self, value):
        self.volume = value

    def resize_window(self):
        self.setFixedSize(self.sizeHint())


# Video settings input window
#   User interface to set the video settings (for computation)
class VideoSettings(QDialog):
    def __init__(self,
                 bw,
                 width,
                 height,
                 color_format,
                 flip_v,
                 flip_h,
                 alignment,
                 playhead_visible,
                 parent=None
                 ):
        super().__init__(parent=parent)
        self.setWindowTitle("Video Settings")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.bw = bw

        self.width = width
        self.height = height
        self.color_format = color_format
        self.flip_v = flip_v
        self.flip_h = flip_h
        self.alignment = alignment
        self.playhead_visible = playhead_visible

        self.width_label = QLabel("Width:")
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(4)
        self.width_entry.setMaximum(1024)
        self.width_entry.setSingleStep(4)
        self.width_entry.setSuffix("px")
        self.width_entry.setValue(self.width)
        self.width_entry.valueChanged.connect(self.width_entry_changed)

        self.height_label = QLabel("Height:")
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(4)
        self.height_entry.setMaximum(1024)
        self.height_entry.setSingleStep(4)
        self.height_entry.setSuffix("px")
        self.height_entry.setValue(self.height)
        self.height_entry.valueChanged.connect(self.height_entry_changed)

        self.color_format_label = QLabel("Color Format:")
        self.color_format_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.color_format_entry = QLineEdit()
        self.color_format_entry.setMaxLength(64)
        self.color_format_entry.setText(self.color_format)
        self.color_format_entry.editingFinished.connect(self.color_format_entry_changed)

        self.alignment_label = QLabel("Audio Alignment::")
        self.alignment_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.alignment_entry = QComboBox()
        self.alignment_entry.addItems(["Frame Start", "Frame Center", "Frame End"])
        if self.alignment == constants.AlignmentCode.START:
            self.alignment_entry.setCurrentIndex(0)
        elif self.alignment == constants.AlignmentCode.MIDDLE:
            self.alignment_entry.setCurrentIndex(1)
        elif self.alignment == constants.AlignmentCode.END:
            self.alignment_entry.setCurrentIndex(2)
        self.alignment_entry.currentIndexChanged.connect(self.alignment_entry_changed)

        self.playhead_entry_label = QLabel("Playhead:")
        self.playhead_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.playhead_entry = QCheckBox("Visible")
        self.playhead_entry.setChecked(self.playhead_visible)
        self.playhead_entry.stateChanged.connect(self.playhead_entry_changed)

        self.flip_v_entry_label = QLabel("Vertical:")
        self.flip_v_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.flip_v_entry = QCheckBox("Flip")
        self.flip_v_entry.setChecked(self.flip_v)
        self.flip_v_entry.stateChanged.connect(self.flip_v_entry_changed)

        self.flip_h_entry_label = QLabel("Horizontal:")
        self.flip_h_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.flip_h_entry = QCheckBox("Flip")
        self.flip_h_entry.setChecked(self.flip_h)
        self.flip_h_entry.stateChanged.connect(self.flip_h_entry_changed)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirm_buttons.accepted.connect(self.accept)
        self.confirm_buttons.rejected.connect(self.reject)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.width_label, 0, 0)
        self.main_layout.addWidget(self.width_entry, 0, 1)
        self.main_layout.addWidget(self.height_label, 1, 0)
        self.main_layout.addWidget(self.height_entry, 1, 1)
        self.main_layout.addWidget(self.color_format_label, 2, 0)
        self.main_layout.addWidget(self.color_format_entry, 2, 1)
        self.main_layout.addWidget(self.alignment_label, 3, 0)
        self.main_layout.addWidget(self.alignment_entry, 3, 1)
        self.main_layout.addWidget(self.playhead_entry_label, 4, 0)
        self.main_layout.addWidget(self.playhead_entry, 4, 1)
        self.main_layout.addWidget(self.flip_v_entry_label, 5, 0)
        self.main_layout.addWidget(self.flip_v_entry, 5, 1)
        self.main_layout.addWidget(self.flip_h_entry_label, 6, 0)
        self.main_layout.addWidget(self.flip_h_entry, 6, 1)
        self.main_layout.addWidget(self.confirm_buttons, 7, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def get_video_settings(self):
        result = dict()
        result["width"] = self.width
        result["height"] = self.height
        result["color_format"] = self.color_format
        result["flip_v"] = self.flip_v
        result["flip_h"] = self.flip_h
        result["alignment"] = self.alignment
        result["playhead_visible"] = self.playhead_visible

        return result

    def width_entry_changed(self, value):
        self.width = value

    def height_entry_changed(self, value):
        self.height = value

    def color_format_entry_changed(self):
        color_format = self.color_format_entry.text()
        parsed = self.bw.parse_color_format(color_format)
        if parsed["is_valid"]:
            self.color_format = color_format
        else:
            self.color_format_entry.setText(self.color_format)
            self.color_format_entry.setFocus()

            error_popup = QMessageBox(parent=self)
            error_popup.setIcon(QMessageBox.Critical)
            error_popup.setText("Invalid Color Format")
            error_popup.setInformativeText(parsed["message"])
            error_popup.setWindowTitle("Error")
            error_popup.exec()

    def playhead_entry_changed(self, value):
        if value == 0:
            self.playhead_visible = False
        else:
            self.playhead_visible = True

    def flip_v_entry_changed(self, value):
        if value == 0:
            self.flip_v = False
        else:
            self.flip_v = True

    def flip_h_entry_changed(self, value):
        if value == 0:
            self.flip_h = False
        else:
            self.flip_h = True

    def alignment_entry_changed(self, idx):
        if idx == 0:
            self.alignment = constants.AlignmentCode.START
        elif idx == 1:
            self.alignment = constants.AlignmentCode.MIDDLE
        elif idx == 2:
            self.alignment = constants.AlignmentCode.END

    def resize_window(self):
        self.setFixedSize(self.sizeHint())


# Player settings input window
#   User interface to set the player settings (for playback)
class PlayerSettings(QDialog):
    def __init__(self,
                 max_view_dim,
                 fps,
                 parent=None
                 ):
        super().__init__(parent=parent)
        self.setWindowTitle("Player Settings")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.max_view_dim = max_view_dim
        self.fps = fps

        self.max_dim_label = QLabel("Max. Dimension:")
        self.max_dim_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.max_dim_entry = QSpinBox()
        self.max_dim_entry.setMinimum(256)
        self.max_dim_entry.setMaximum(7680)
        self.max_dim_entry.setSingleStep(64)
        self.max_dim_entry.setSuffix("px")
        self.max_dim_entry.setValue(self.max_view_dim)
        self.max_dim_entry.valueChanged.connect(self.max_dim_entry_changed)

        self.fps_label = QLabel("Framerate:")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.fps_entry = QSpinBox()
        self.fps_entry.setMinimum(1)
        self.fps_entry.setMaximum(120)
        self.fps_entry.setSingleStep(1)
        self.fps_entry.setSuffix("fps")
        self.fps_entry.setValue(self.fps)
        self.fps_entry.valueChanged.connect(self.fps_entry_changed)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirm_buttons.accepted.connect(self.accept)
        self.confirm_buttons.rejected.connect(self.reject)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.max_dim_label, 0, 0)
        self.main_layout.addWidget(self.max_dim_entry, 0, 1)
        self.main_layout.addWidget(self.fps_label, 1, 0)
        self.main_layout.addWidget(self.fps_entry, 1, 1)
        self.main_layout.addWidget(self.confirm_buttons, 2, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def get_player_settings(self):
        result = dict()
        result["max_view_dim"] = self.max_view_dim
        result["fps"] = self.fps

        return result

    def max_dim_entry_changed(self, value):
        self.max_view_dim = value

    def fps_entry_changed(self, value):
        self.fps = value

    def resize_window(self):
        self.setFixedSize(self.sizeHint())


# Export image dialog
#   User interface to export a single frame
class ExportFrame(QDialog):
    def __init__(self,
                 width,
                 height,
                 parent=None
                 ):
        super().__init__(parent=parent)
        self.setWindowTitle("Export Image Settings")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.width = width
        self.height = height
        self.keep_aspect = False

        self.width_label = QLabel("Export Width:")
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(64)
        self.width_entry.setMaximum(7680)
        self.width_entry.setSingleStep(64)
        self.width_entry.setSuffix("px")
        self.width_entry.setValue(self.width)
        self.width_entry.valueChanged.connect(self.width_entry_changed)

        self.height_label = QLabel("Export Height:")
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(64)
        self.height_entry.setMaximum(7680)
        self.height_entry.setSingleStep(64)
        self.height_entry.setSuffix("px")
        self.height_entry.setValue(self.height)
        self.height_entry.valueChanged.connect(self.height_entry_changed)

        self.aspect_label = QLabel("Aspect Ratio:")
        self.aspect_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.aspect_entry = QCheckBox("Force")
        self.aspect_entry.setChecked(self.keep_aspect)
        self.aspect_entry.stateChanged.connect(self.aspect_entry_changed)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirm_buttons.accepted.connect(self.accept)
        self.confirm_buttons.rejected.connect(self.reject)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.width_label, 0, 0)
        self.main_layout.addWidget(self.width_entry, 0, 1)
        self.main_layout.addWidget(self.height_label, 1, 0)
        self.main_layout.addWidget(self.height_entry, 1, 1)
        self.main_layout.addWidget(self.aspect_label, 2, 0)
        self.main_layout.addWidget(self.aspect_entry, 2, 1)
        self.main_layout.addWidget(self.confirm_buttons, 3, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self):
        self.setFixedSize(self.sizeHint())

    def get_settings(self):
        result = dict()
        result["width"] = self.width
        result["height"] = self.height
        result["keep_aspect"] = self.keep_aspect

        return result

    def width_entry_changed(self, value):
        self.width = value

    def height_entry_changed(self, value):
        self.height = value

    def aspect_entry_changed(self, value):
        if value == 0:
            self.keep_aspect = False
        else:
            self.keep_aspect = True


# Export image sequence dialog
#   User interface to export an image sequence
class ExportSequence(QDialog):
    def __init__(self,
                 width,
                 height,
                 parent=None
                 ):
        super().__init__(parent=parent)
        self.setWindowTitle("Export Sequence Settings")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.width = width
        self.height = height
        self.fps = 60.0
        self.keep_aspect = False
        self.format = constants.ImageFormatCode.PNG

        self.fps_label = QLabel("FPS:")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.fps_entry = QDoubleSpinBox()
        self.fps_entry.setMinimum(1.0)
        self.fps_entry.setMaximum(120.0)
        self.fps_entry.setSingleStep(1.0)
        self.fps_entry.setSuffix("fps")
        self.fps_entry.setValue(self.fps)
        self.fps_entry.valueChanged.connect(self.fps_entry_changed)

        self.width_label = QLabel("Export Width:")
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(64)
        self.width_entry.setMaximum(7680)
        self.width_entry.setSingleStep(64)
        self.width_entry.setSuffix("px")
        self.width_entry.setValue(self.width)
        self.width_entry.valueChanged.connect(self.width_entry_changed)

        self.height_label = QLabel("Export Height:")
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(64)
        self.height_entry.setMaximum(7680)
        self.height_entry.setSingleStep(64)
        self.height_entry.setSuffix("px")
        self.height_entry.setValue(self.height)
        self.height_entry.valueChanged.connect(self.height_entry_changed)

        self.aspect_label = QLabel("Aspect Ratio:")
        self.aspect_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.aspect_entry = QCheckBox("Force")
        self.aspect_entry.setChecked(self.keep_aspect)
        self.aspect_entry.stateChanged.connect(self.aspect_entry_changed)

        self.format_label = QLabel("Image Format:")
        self.format_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.format_entry = QComboBox()
        self.format_entry.addItems(["PNG (.png)", "JPEG (.jpg)", "BMP (.bmp)"])
        if self.format == constants.ImageFormatCode.PNG:
            self.format_entry.setCurrentIndex(0)
        elif self.format == constants.ImageFormatCode.JPEG:
            self.format_entry.setCurrentIndex(1)
        elif self.format == constants.ImageFormatCode.BITMAP:
            self.format_entry.setCurrentIndex(2)
        self.format_entry.currentIndexChanged.connect(self.format_entry_changed)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirm_buttons.accepted.connect(self.accept)
        self.confirm_buttons.rejected.connect(self.reject)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.fps_label, 0, 0)
        self.main_layout.addWidget(self.fps_entry, 0, 1)
        self.main_layout.addWidget(self.width_label, 1, 0)
        self.main_layout.addWidget(self.width_entry, 1, 1)
        self.main_layout.addWidget(self.height_label, 2, 0)
        self.main_layout.addWidget(self.height_entry, 2, 1)
        self.main_layout.addWidget(self.aspect_label, 3, 0)
        self.main_layout.addWidget(self.aspect_entry, 3, 1)
        self.main_layout.addWidget(self.format_label, 4, 0)
        self.main_layout.addWidget(self.format_entry, 4, 1)
        self.main_layout.addWidget(self.confirm_buttons, 5, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self):
        self.setFixedSize(self.sizeHint())

    def get_settings(self):
        result = dict()
        result["width"] = self.width
        result["height"] = self.height
        result["fps"] = self.fps
        result["keep_aspect"] = self.keep_aspect
        result["format"] = self.format

        return result

    def width_entry_changed(self, value):
        self.width = value

    def height_entry_changed(self, value):
        self.height = value

    def aspect_entry_changed(self, value):
        if value == 0:
            self.keep_aspect = False
        else:
            self.keep_aspect = True

    def fps_entry_changed(self, value):
        self.fps = value

    def format_entry_changed(self, value):
        if value == 0:
            self.format = constants.ImageFormatCode.PNG
        elif value == 1:
            self.format = constants.ImageFormatCode.JPEG
        elif value == 2:
            self.format = constants.ImageFormatCode.BITMAP


# Export video dialog
#   User interface to export a video
class ExportVideo(QDialog):
    def __init__(self,
                 width,
                 height,
                 parent=None
                 ):
        super().__init__(parent=parent)
        self.setWindowTitle("Export Video Settings")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.width = width
        self.height = height
        self.fps = 60.0
        self.keep_aspect = False

        self.fps_label = QLabel("FPS:")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.fps_entry = QDoubleSpinBox()
        self.fps_entry.setMinimum(1.0)
        self.fps_entry.setMaximum(120.0)
        self.fps_entry.setSingleStep(1.0)
        self.fps_entry.setSuffix("fps")
        self.fps_entry.setValue(self.fps)
        self.fps_entry.valueChanged.connect(self.fps_entry_changed)

        self.width_label = QLabel("Export Width:")
        self.width_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.width_entry = QSpinBox()
        self.width_entry.setMinimum(64)
        self.width_entry.setMaximum(7680)
        self.width_entry.setSingleStep(64)
        self.width_entry.setSuffix("px")
        self.width_entry.setValue(self.width)
        self.width_entry.valueChanged.connect(self.width_entry_changed)

        self.height_label = QLabel("Export Height:")
        self.height_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.height_entry = QSpinBox()
        self.height_entry.setMinimum(64)
        self.height_entry.setMaximum(7680)
        self.height_entry.setSingleStep(64)
        self.height_entry.setSuffix("px")
        self.height_entry.setValue(self.height)
        self.height_entry.valueChanged.connect(self.height_entry_changed)

        self.aspect_label = QLabel("Aspect Ratio:")
        self.aspect_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.aspect_entry = QCheckBox("Force")
        self.aspect_entry.setChecked(self.keep_aspect)
        self.aspect_entry.stateChanged.connect(self.aspect_entry_changed)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirm_buttons.accepted.connect(self.accept)
        self.confirm_buttons.rejected.connect(self.reject)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.fps_label, 0, 0)
        self.main_layout.addWidget(self.fps_entry, 0, 1)
        self.main_layout.addWidget(self.width_label, 1, 0)
        self.main_layout.addWidget(self.width_entry, 1, 1)
        self.main_layout.addWidget(self.height_label, 2, 0)
        self.main_layout.addWidget(self.height_entry, 2, 1)
        self.main_layout.addWidget(self.aspect_label, 3, 0)
        self.main_layout.addWidget(self.aspect_entry, 3, 1)
        self.main_layout.addWidget(self.confirm_buttons, 4, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self):
        self.setFixedSize(self.sizeHint())

    def get_settings(self):
        result = dict()
        result["width"] = self.width
        result["height"] = self.height
        result["fps"] = self.fps
        result["keep_aspect"] = self.keep_aspect

        return result

    def width_entry_changed(self, value):
        self.width = value

    def height_entry_changed(self, value):
        self.height = value

    def aspect_entry_changed(self, value):
        if value == 0:
            self.keep_aspect = False
        else:
            self.keep_aspect = True

    def fps_entry_changed(self, value):
        self.fps = value


# Export video encoder settings dialog
#   User interface to set encoder settings when exporting a video
class VideoEncoderSettings(QDialog):
    def __init__(self,
                 video_format,
                 parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Video Encoder Settings")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.video_format = video_format

        # Set defaults
        if self.video_format == constants.VideoFormatCode.MP4:
            self.codec = constants.VideoCodecCode.LIBX264
        elif self.video_format == constants.VideoFormatCode.AVI:
            self.codec = constants.VideoCodecCode.PNG
        self.audio_codec = constants.AudioCodecCode.MP3
        self.preset = constants.EncoderPresetCode.ULTRAFAST

        self.codec_entry_label = QLabel("Video Codec:")
        self.codec_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.codec_entry = QComboBox()
        if self.video_format == constants.VideoFormatCode.MP4:
            self.codec_entry.addItems(["LIBX264", "MPEG4"])
            if self.codec == constants.VideoCodecCode.LIBX264:
                self.codec_entry.setCurrentIndex(0)
            elif self.codec == constants.VideoCodecCode.MPEG4:
                self.codec_entry.setCurrentIndex(1)
        elif self.video_format == constants.VideoFormatCode.AVI:
            self.codec_entry.addItems(["PNG", "Raw"])
            if self.codec == constants.VideoCodecCode.PNG:
                self.codec_entry.setCurrentIndex(0)
            elif self.codec == constants.VideoCodecCode.RAW:
                self.codec_entry.setCurrentIndex(1)
        self.codec_entry.currentIndexChanged.connect(self.codec_entry_changed)

        self.audio_codec_entry_label = QLabel("Audio Codec:")
        self.audio_codec_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.audio_codec_entry = QComboBox()
        self.audio_codec_entry.addItems(["MP3", "M4A", "WAV 16-bit", "WAV 32-bit"])
        if self.audio_codec == constants.AudioCodecCode.MP3:
            self.audio_codec_entry.setCurrentIndex(0)
        elif self.audio_codec == constants.AudioCodecCode.M4A:
            self.audio_codec_entry.setCurrentIndex(1)
        elif self.audio_codec == constants.AudioCodecCode.WAV16:
            self.audio_codec_entry.setCurrentIndex(2)
        elif self.audio_codec == constants.AudioCodecCode.WAV32:
            self.audio_codec_entry.setCurrentIndex(3)
        self.audio_codec_entry.currentIndexChanged.connect(self.audio_codec_entry_changed)

        self.preset_entry_label = QLabel("Encoder Preset:")
        self.preset_entry_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.preset_entry = QComboBox()
        self.preset_entry.addItems([
            "Ultra Fast",
            "Super Fast",
            "Very Fast",
            "Faster",
            "Fast",
            "Medium",
            "Slow",
            "Slower",
            "Very Slow",
            "Placebo"
        ])
        if self.preset == constants.EncoderPresetCode.ULTRAFAST:
            self.preset_entry.setCurrentIndex(0)
        elif self.preset == constants.EncoderPresetCode.SUPERFAST:
            self.preset_entry.setCurrentIndex(1)
        elif self.preset == constants.EncoderPresetCode.VERYFAST:
            self.preset_entry.setCurrentIndex(2)
        elif self.preset == constants.EncoderPresetCode.FASTER:
            self.preset_entry.setCurrentIndex(3)
        elif self.preset == constants.EncoderPresetCode.FAST:
            self.preset_entry.setCurrentIndex(4)
        elif self.preset == constants.EncoderPresetCode.MEDIUM:
            self.preset_entry.setCurrentIndex(5)
        elif self.preset == constants.EncoderPresetCode.SLOW:
            self.preset_entry.setCurrentIndex(6)
        elif self.preset == constants.EncoderPresetCode.SLOWER:
            self.preset_entry.setCurrentIndex(7)
        elif self.preset == constants.EncoderPresetCode.VERYSLOW:
            self.preset_entry.setCurrentIndex(8)
        elif self.preset == constants.EncoderPresetCode.PLACEBO:
            self.preset_entry.setCurrentIndex(9)
        self.preset_entry.currentIndexChanged.connect(self.preset_entry_changed)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirm_buttons.accepted.connect(self.accept)
        self.confirm_buttons.rejected.connect(self.reject)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.codec_entry_label, 0, 0)
        self.main_layout.addWidget(self.codec_entry, 0, 1)
        self.main_layout.addWidget(self.audio_codec_entry_label, 1, 0)
        self.main_layout.addWidget(self.audio_codec_entry, 1, 1)
        self.main_layout.addWidget(self.preset_entry_label, 2, 0)
        self.main_layout.addWidget(self.preset_entry, 2, 1)
        self.main_layout.addWidget(self.confirm_buttons, 3, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self):
        self.setFixedSize(self.sizeHint())

    def get_settings(self):
        result = dict()
        result["codec"] = self.codec
        result["audio_codec"] = self.audio_codec
        result["preset"] = self.preset

        return result

    def codec_entry_changed(self, value):
        if self.video_format == constants.VideoFormatCode.MP4:
            if value == 0:
                self.codec = constants.VideoCodecCode.LIBX264
            elif value == 1:
                self.codec = constants.VideoCodecCode.MPEG4
        elif self.video_format == constants.VideoFormatCode.AVI:
            if value == 0:
                self.codec = constants.VideoCodecCode.PNG
            elif value == 1:
                self.codec = constants.VideoCodecCode.RAW

    def audio_codec_entry_changed(self, value):
        if value == 0:
            self.audio_codec = constants.AudioCodecCode.MP3
        elif value == 1:
            self.audio_codec = constants.AudioCodecCode.M4A
        elif value == 2:
            self.audio_codec = constants.AudioCodecCode.WAV16
        elif value == 3:
            self.audio_codec = constants.AudioCodecCode.WAV32

    def preset_entry_changed(self, value):
        if value == 0:
            self.preset = constants.EncoderPresetCode.ULTRAFAST
        elif value == 1:
            self.preset = constants.EncoderPresetCode.SUPERFAST
        elif value == 2:
            self.preset = constants.EncoderPresetCode.VERYFAST
        elif value == 3:
            self.preset = constants.EncoderPresetCode.FASTER
        elif value == 4:
            self.preset = constants.EncoderPresetCode.FAST
        elif value == 5:
            self.preset = constants.EncoderPresetCode.MEDIUM
        elif value == 6:
            self.preset = constants.EncoderPresetCode.SLOW
        elif value == 7:
            self.preset = constants.EncoderPresetCode.SLOWER
        elif value == 8:
            self.preset = constants.EncoderPresetCode.VERYSLOW
        elif value == 9:
            self.preset = constants.EncoderPresetCode.PLACEBO


# Hotkey info dialog
#   Lists the program hotkeys
class HotkeysInfo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Hotkey Info")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.play_label = QLabel("Play / Pause:")
        self.play_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.play_key_label = QLabel("Spacebar")
        self.play_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.forward_label = QLabel("Forward:")
        self.forward_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.forward_key_label = QLabel("Right")
        self.forward_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.back_label = QLabel("Back:")
        self.back_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.back_key_label = QLabel("Left")
        self.back_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.frame_forward_label = QLabel("Frame Forward:")
        self.frame_forward_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.frame_forward_key_label = QLabel(">")
        self.frame_forward_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.frame_back_label = QLabel("Frame Back:")
        self.frame_back_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.frame_back_key_label = QLabel("<")
        self.frame_back_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.restart_label = QLabel("Restart:")
        self.restart_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.restart_key_label = QLabel("R")
        self.restart_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.volume_up_label = QLabel("Volume Up:")
        self.volume_up_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.volume_up_key_label = QLabel("Up")
        self.volume_up_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.volume_down_label = QLabel("Volume Down:")
        self.volume_down_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.volume_down_key_label = QLabel("Down")
        self.volume_down_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.mute_label = QLabel("Mute:")
        self.mute_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)

        self.mute_key_label = QLabel("M")
        self.mute_key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        self.confirm_buttons.accepted.connect(self.accept)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.play_label, 0, 0)
        self.main_layout.addWidget(self.play_key_label, 0, 1)
        self.main_layout.addWidget(self.back_label, 1, 0)
        self.main_layout.addWidget(self.back_key_label, 1, 1)
        self.main_layout.addWidget(self.forward_label, 2, 0)
        self.main_layout.addWidget(self.forward_key_label, 2, 1)
        self.main_layout.addWidget(self.frame_back_label, 3, 0)
        self.main_layout.addWidget(self.frame_back_key_label, 3, 1)
        self.main_layout.addWidget(self.frame_forward_label, 4, 0)
        self.main_layout.addWidget(self.frame_forward_key_label, 4, 1)
        self.main_layout.addWidget(self.restart_label, 5, 0)
        self.main_layout.addWidget(self.restart_key_label, 5, 1)
        self.main_layout.addWidget(self.volume_up_label, 6, 0)
        self.main_layout.addWidget(self.volume_up_key_label, 6, 1)
        self.main_layout.addWidget(self.volume_down_label, 7, 0)
        self.main_layout.addWidget(self.volume_down_key_label, 7, 1)
        self.main_layout.addWidget(self.mute_label, 8, 0)
        self.main_layout.addWidget(self.mute_key_label, 8, 1)
        self.main_layout.addWidget(self.confirm_buttons, 9, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self):
        self.setFixedSize(self.sizeHint())


# About dialog
#   Gives info about the program
class About(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(f"About {constants.TITLE}")
        self.setWindowIcon(QIcon(constants.ICON_PATHS["program"]))

        # Hide "?" button
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowContextHelpButtonHint)

        self.icon_size = 200

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setPixmap(QPixmap(constants.ICON_PATHS["program"]))
        self.icon_label.setScaledContents(True)
        self.icon_label.setFixedSize(self.icon_size, self.icon_size)

        self.about_text = QLabel(
            f"{constants.TITLE} v{constants.VERSION}\nby {constants.COPYRIGHT}\n© Copyright 2026\n\n"
            f"{constants.DESCRIPTION}\n\n"
            f"Project Home Page:\n{constants.PROJECT_URL}\n\n"
            f"Donate:\n{constants.DONATE_URL}")
        self.about_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.confirm_buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        self.confirm_buttons.accepted.connect(self.accept)

        self.main_layout = QGridLayout()

        self.main_layout.addWidget(self.icon_label, 0, 0, 2, 1)
        self.main_layout.addWidget(self.about_text, 0, 1)
        self.main_layout.addWidget(self.confirm_buttons, 1, 0, 1, 2)

        self.setLayout(self.main_layout)

        self.resize_window()

    def resize_window(self):
        self.setFixedSize(self.sizeHint())
