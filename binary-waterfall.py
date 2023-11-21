#!/usr/bin/env python3

import os
import sys
import argparse
from enum import Enum
import yaml
import shutil
import math
import wave
import audioop
import mutagen.wave
import cv2
import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QGridLayout, QLabel, QPushButton,
    QFileDialog
)
from PyQt6.QtGui import (
    QImage, QPixmap,
    QAction, QIcon
)

# Test if this is a PyInstaller executable or a .py file
if getattr(sys, 'frozen', False):
    IS_EXE = True
    PROG_FILE = sys.executable
    PROG_PATH = os.path.dirname(PROG_FILE)
    PATH = sys._MEIPASS
else:
    IS_EXE = False
    PROG_FILE = os.path.realpath(__file__)
    PROG_PATH = os.path.dirname(PROG_FILE)
    PATH = PROG_PATH

# Read program version file
VERSION_FILE = os.path.join(PATH, "version.yml")
with open(VERSION_FILE, "r") as f:
    version_file_dict = yaml.safe_load(f)
    
    VERSION = version_file_dict["Version"]
    DESCRIPTION = version_file_dict["FileDescription"]
    TITLE = version_file_dict["ProductName"]
    COPYRIGHT = version_file_dict["LegalCopyright"]
    
    del(version_file_dict)


# The path to the program's resources
RESOURCE_PATH = os.path.join(PATH, "resources")

# A dict to store icon locations
ICON_PATH = {
    "play": os.path.join(RESOURCE_PATH, "play.png"),
    "pause": os.path.join(RESOURCE_PATH, "pause.png"),
    "back": os.path.join(RESOURCE_PATH, "back.png"),
    "forward": os.path.join(RESOURCE_PATH, "forward.png"),
    "restart": os.path.join(RESOURCE_PATH, "restart.png")
}

# Binary Waterfall abstraction class
#   Provides an abstract object for converting binary files
#   into audio files and image frames. This object does not
#   track time or handle playback, it only provides resources
#   to other code in order to produce the videos
class BinaryWaterfall:
    def __init__(self,
        filename=None,
        width=48,
        height=48,
        color_format_string="bgrx",
        num_channels=1,
        sample_bytes=1,
        sample_rate=32000,
        volume=100
    ):
        self.audio_filename = None  # Pre-init this to make sure delete_audio works
        self.set_filename(filename=filename)
        
        self.set_visual_settings(
            width=width,
            height=height,
            color_format_string=color_format_string
        )
        
        self.set_audio_settings(
            num_channels=num_channels,
            sample_bytes=sample_bytes,
            sample_rate=sample_rate,
            volume=volume
        )
    
    def __del__(self):
        self.cleanup()
    
    def set_filename(self, filename):
        # Delete current audio file if it exists
        self.delete_audio()
        
        if filename == None:
            # Reset all vars
            self.filename = None
            self.bytes = None
            self.total_bytes = None
            self.audio_filename = None
            return
        
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: \"{filename}\"")
        
        self.filename = os.path.realpath(filename)
        
        # Load bytes
        with open(self.filename, "rb") as f:
            self.bytes = f.read()
        self.total_bytes = len(self.bytes)
        
        # Compute audio file name
        file_path, file_main_name = os.path.split(self.filename)
        self.audio_filename = os.path.join(
            PATH,
            file_main_name + os.path.extsep + "wav"
        )
    
    class ColorFmtCode(Enum):
        RED = "r"
        GREEN = "g"
        BLUE = "b"
        UNUSED = "x"
        VALID_OPTIONS = "rgbx"
    
    def set_visual_settings(self,
        width,
        height,
        color_format_string
    ):
        if width < 4:
            raise ValueError("Visualization width must be at least 4")
        
        if height < 4:
            raise ValueError("Visualization height must be at least 4")
        
        color_format_string = color_format_string.strip().lower()
        red_count = color_format_string.count(self.ColorFmtCode.RED.value)
        if red_count != 1:
            raise ValueError(f"Exactly 1 red channel format specifier \"{self.ColorFmtCode.RED.value}\" needed, but {red_count} were given in format string \"{color_format_string}\"")
        green_count = color_format_string.count(self.ColorFmtCode.GREEN.value)
        if green_count != 1:
            raise ValueError(f"Exactly 1 green channel format specifier \"{self.ColorFmtCode.GREEN.value}\" needed, but {green_count} were given in format string \"{color_format_string}\"")
        blue_count = color_format_string.count(self.ColorFmtCode.BLUE.value)
        if blue_count != 1:
            raise ValueError(f"Exactly 1 blue channel format specifier \"{self.ColorFmtCode.BLUE.value}\" needed, but {blue_count} were given in format string \"{color_format_string}\"")
        unused_count = color_format_string.count(self.ColorFmtCode.UNUSED.value)
        
        color_format_list = list()
        for c in color_format_string:
            if c not in self.ColorFmtCode.VALID_OPTIONS.value:
                raise ValueError(f"Color formatting codes only accept \"{self.ColorFmtCode.RED.value}\" = red, \"{self.ColorFmtCode.GREEN.value}\" = green, \"{self.ColorFmtCode.BLUE.value}\" = blue, \"{self.ColorFmtCode.UNUSED.value}\" = unused")
            
            if c == self.ColorFmtCode.RED.value:
                color_format_list.append(self.ColorFmtCode.RED)
            elif c == self.ColorFmtCode.GREEN.value:
                color_format_list.append(self.ColorFmtCode.GREEN)
            elif c == self.ColorFmtCode.BLUE.value:
                color_format_list.append(self.ColorFmtCode.BLUE)
            elif c == self.ColorFmtCode.UNUSED.value:
                color_format_list.append(self.ColorFmtCode.UNUSED)
        
        self.width = width
        self.height = height
        self.dim = (self.width, self.height)
        self.used_color_bytes = red_count + green_count + blue_count
        self.unused_color_bytes = unused_count
        self.color_bytes = self.used_color_bytes + self.unused_color_bytes
        self.color_format = color_format_list
    
    def set_audio_settings(self,
        num_channels,
        sample_bytes,
        sample_rate,
        volume
    ):
        if num_channels not in [1, 2]:
            raise ValueError("Invalid number of audio channels, must be either 1 or 2")
        
        if sample_bytes not in [1, 2, 3, 4]:
            raise ValueError("Invalid sample size (bytes), must be either 1, 2, 3, or 4")
        
        if sample_rate < 1:
            raise ValueError("Invalid sample rate, must be at least 1")
        
        if volume < 0 or volume > 100:
            raise ValueError("Volume must be between 0 and 100")
        
        self.num_channels = num_channels
        self.sample_bytes = sample_bytes
        self.sample_rate = sample_rate
        self.volume = volume
        
        # Re-compute audio file
        self.compute_audio()
    
    def delete_audio(self):
        if self.audio_filename == None:
            # Do nothing
            return
        try:
            os.remove(self.audio_filename)
        except FileNotFoundError:
            pass
    
    def compute_audio(self):
        if self.filename == None:
            # If there is no file set, reset the vars
            self.audio_length_ms = None
            return
        
        # Delete current file if it exists
        self.delete_audio()
        
        # Compute the new file (full volume)
        with wave.open(self.audio_filename, "wb") as f:
            f.setnchannels(self.num_channels)
            f.setsampwidth(self.sample_bytes)
            f.setframerate(self.sample_rate)
            f.writeframesraw(self.bytes)
        
        if self.volume != 100:
            # Reduce the audio volume
            factor = self.volume / 100
            temp_filename = self.audio_filename + ".temp"
            with wave.open(self.audio_filename, "rb") as f:
                p = f.getparams()
                with wave.open(temp_filename , "wb") as tempfile:
                    tempfile.setparams(p)
                    frames = f.readframes(p.nframes)
                    tempfile.writeframesraw(audioop.mul(frames, p.sampwidth, factor))
            self.delete_audio()
            shutil.move(temp_filename, self.audio_filename)
        
        # Get audio length
        audio_length = mutagen.wave.WAVE(self.audio_filename).info.length
        self.audio_length_ms = math.ceil(audio_length * 1000)
    
    def change_filename(self, new_filename):
        self.set_filename(new_filename)
        self.compute_audio()
    
    def get_address(self, ms):
        address_block_size = self.width * self.color_bytes
        total_blocks = math.ceil(self.total_bytes / address_block_size)
        address_block_offset = round(ms * total_blocks / self.audio_length_ms)
        return address_block_offset * address_block_size
    
    # A 1D Python byte string
    def get_frame_bytestring(self, ms):
        picture_bytes = bytes()
        current_address = self.get_address(ms)
        for row in range(self.height):
            for col in range(self.width):
                # Fill one BGR byte value
                this_byte = [b'\x00', b'\x00', b'\x00']
                for c in self.color_format:
                    if c == self.ColorFmtCode.RED:
                        this_byte[0] = self.bytes[current_address:current_address+1] # Red
                    elif c == self.ColorFmtCode.GREEN:
                        this_byte[1] = self.bytes[current_address:current_address+1] # Green
                    elif c == self.ColorFmtCode.BLUE:
                        this_byte[2] = self.bytes[current_address:current_address+1] # Blue
                    
                    current_address += 1
                
                picture_bytes += b"".join(this_byte)
        
        full_length = (self.width * self.height * self.used_color_bytes)
        picture_bytes_length = len(picture_bytes)
        # Pad picture data if we're near the end of the file
        if picture_bytes_length < full_length:
            pad_length = full_length - picture_bytes_length
            picture_bytes += b"\x00" * pad_length

        return picture_bytes
    
    # A 3D Nympy array (RGB)
    def get_frame_array(self, ms, flip=True):
        frame_bytesring = self.get_frame_bytestring(ms)
        frame_np = np.frombuffer(frame_bytesring, dtype=np.uint8)
        frame_array = frame_np.reshape((self.width, self.height, 3))
        if flip:
            # Flip vertically
            frame_array = np.flip(frame_array, axis=0)
        
        return frame_array
    
    # A PIL Image (RGB)
    def get_frame_image(self, ms, flip=True):
        frame_array = self.get_frame_array(ms, flip=flip)
        img = Image.fromarray(frame_array)
        
        return img
    
    def cleanup(self):
        self.delete_audio()

# My QMainWindow class
#   Used to customize the main window.
#   The actual object used to programmatically reference
#   the "main window" is MainWindow
class MyQMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{TITLE}")
        
        self.player_label = QLabel(parent=self)
        self.player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.player = Player(self.player_label)
        
        self.transport_height = 40
        
        self.transport_play = QPushButton(parent=self, text="Play")
        self.transport_play.setFixedHeight(self.transport_height)
        self.transport_play.clicked.connect(self.play_clicked)
        
        self.transport_forward = QPushButton(parent=self, text="5S >")
        self.transport_forward.setFixedHeight(self.transport_height)
        self.transport_forward.clicked.connect(self.forward_clicked)
        
        self.transport_back = QPushButton(parent=self, text="< 5S")
        self.transport_back.setFixedHeight(self.transport_height)
        self.transport_back.clicked.connect(self.back_clicked)
        
        self.transport_restart = QPushButton(parent=self, text="Restart")
        self.transport_restart.setFixedHeight(self.transport_height)
        self.transport_restart.clicked.connect(self.restart_clicked)
        
        self.error_label = QLabel(parent=self)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #666")
        
        self.main_layout = QGridLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
        
        self.main_layout.addWidget(self.player_label, 0, 0, 1, 5)
        self.main_layout.addWidget(self.transport_restart, 1, 0)
        self.main_layout.addWidget(self.transport_back, 1, 1)
        self.main_layout.addWidget(self.transport_play, 1, 2)
        self.main_layout.addWidget(self.transport_forward, 1, 3)
        self.main_layout.addWidget(self.error_label, 1, 4)
        
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        
        self.main_menu = self.menuBar()
        
        self.file_menu = self.main_menu.addMenu("&File")
        
        self.file_menu_open = QAction(QIcon.fromTheme("document-open"), "&Open...", self)
        self.file_menu_open.triggered.connect(self.open_file_clicked)
        self.file_menu.addAction(self.file_menu_open)
        
        self.file_menu_close = QAction(QIcon.fromTheme("window-close"), "&Close", self)
        self.file_menu_close.triggered.connect(self.close_file_clicked)
        self.file_menu.addAction(self.file_menu_close)
        
        
        # Set window to content size
        self.resize_window()
    
    def resize_window(self):
        self.setFixedSize(self.sizeHint())
    
    def set_error(self, error_text):
        self.error_label.setText(error_text)
    
    def set_play_button(self, play):
        if play:
            self.transport_play.setText("Play")
        else:
            self.transport_play.setText("Pause")
    
    def pause_player(self):
        self.player.pause()
        self.set_play_button(play=True) #TODO: Update with the player state somehow
    
    def play_player(self):
        self.player.play()
        self.set_play_button(play=False) #TODO: Update with the player state somehow
    
    def play_clicked(self):
        if self.player.is_playing():
            # Already playing, pause
            self.pause_player()
        else:
            # Paused, start playing
            self.play_player()
    
    def forward_clicked(self):
        self.player.forward()
    
    def back_clicked(self):
        self.player.back()
    
    def restart_clicked(self):
        self.player.restart()
    
    def open_file_clicked(self):
        self.pause_player()
        
        filename, filetype = QFileDialog.getOpenFileName(
            self,
            "Open File",
            PROG_PATH,
            "All Binary Files (*)"
        )
        
        if filename != "":
            self.player.open_file(filename=filename)
            file_path, file_title = os.path.split(filename)
            self.setWindowTitle(f"{TITLE} | {file_title}")
    
    def close_file_clicked(self):
        self.pause_player()
        
        self.player.close_file()
        self.setWindowTitle(f"{TITLE}")
    
    #TODO: Sync the image to the audio
    #TODO: Add transport bar (read-only)
    #TODO: Make transport bar seekable
    

# Image playback class
#   Provides an abstraction for displaying images and audio in the GUI
class Player:
    def __init__(self,
        label,
        width=600,
        height=600
    ):
        self.label = label
        
        self.set_dims(width=width, height=height)
        
        # Initialize player as black
        self.clear_image()
        
        # Make the BinaryWaterfall class
        self.bw = BinaryWaterfall()
        
        # Make the QMediaPlayer for audio playback
        self.audio = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.audio.setAudioOutput(self.audio_output)
        
        # Set audio playback settings
        self.set_volume(100)
        
    
    def set_dims(self, width, height):
        self.width = width
        self.height = height
        self.dim = (self.width, self.height)
    
    def clear_image(self):
        black_image = Image.new(
            mode="RGB",
            size=self.dim,
            color=(0,0,0)
        )
        self.set_image(black_image)
    
    def update_dims(self, width, height):
        # Change dims
        self.set_dims(width=width, height=height)
        
        # Update image
        self.set_image(self.image)
    
    def set_volume(self, volume):
        self.audio_output.setVolume(volume)
    
    def scale_image(self, image):
        return image.resize(self.dim, Image.NEAREST)
    
    def set_image(self, image):
        self.image = self.scale_image(image).convert("RGBA")
        
        # Compute the QPixmap version
        qimage = ImageQt(self.image)
        qpixmap = QPixmap.fromImage(qimage)
        
        # Set the picture
        self.label.setPixmap(qpixmap)
    
    def get_position(self):
        return self.audio.position()
    
    def get_duration(self):
        return self.audio.duration()
    
    def set_position(self, ms):
        duration = self.get_duration()
        
        # Validate it's in range, and if it's not, clip it
        ms = math.ceil(ms)
        if ms < 0:
            ms = 0
        if ms > duration:
            ms = duration
        
        #TODO: If the file is at the end, pause
        
        self.position = ms
        if self.bw.filename == None:
            self.clear_image() #TODO: Update elsewhere
        else:
            self.set_image(self.bw.get_frame_image(self.position)) #TODO: Update elsewhere
            self.audio.setPosition(ms)
            
    
    def play(self):
        self.audio.play()
    
    def pause(self):
        self.audio.pause()
    
    def forward(self, ms=5000):
        new_pos = self.position + ms
        self.set_position(new_pos)
    
    def back(self, ms=5000):
        new_pos = self.position - ms
        self.set_position(new_pos)
    
    def restart(self):
        self.set_position(0)
    
    def open_file(self, filename):
        self.pause()
        
        self.bw.set_filename(filename)
        self.bw.compute_audio()
        
        if self.bw.audio_filename == None:
            self.audio.setSource(QUrl(None))
        else:
            self.audio.setSource(QUrl.fromLocalFile(self.bw.audio_filename))
        
        self.restart()
    
    def close_file(self):
        self.open_file(filename=None)
    
    def file_is_open(self):
        if self.bw.filename == None:
            return False
        else:
            return True
    
    def is_playing(self):
        return self.audio.isPlaying()
    

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



# A helper function for the argument parser
def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)

# Parse arguments
def parse_args(args):
    parser = argparse.ArgumentParser(
        description=f"{DESCRIPTION}\n\nDefault parameters are shown in [brackets].",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    '''
    parser.add_argument("-1", "--first", dest="first_arg", type=float, required=True,
        help="the first argument")
    parser.add_argument("-2", "--second", dest="second_arg", type=float, required=False, default=1.0,
        help="the second argument [1]")
    parser.add_argument("-o", "--operaton", dest="opcode", type=str, required=False, default="+",
        help="the operation to perform on the arguments, either \"+\", \"-\", \"*\", or \"/\" [+]")
    '''
    
    parsed_args, unparsed_args = parser.parse_known_args()
    return parsed_args, unparsed_args

def main(args):
    parsed_args, unparsed_args = parse_args(args)
    qt_args = [sys.argv[0]] + unparsed_args
    
    main_window = MainWindow(qt_args)
    main_window.run()

def run():
    main(sys.argv[1:])

if __name__ == "__main__":
    run()
