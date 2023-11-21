#!/usr/bin/env python3

import os
import sys
import argparse
from enum import Enum
import shutil
import math
import wave
import audioop
import mutagen.wave
import cv2
import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QGridLayout, QLabel
)
from PyQt6.QtGui import (
    QImage, QPixmap
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



# A dict to store icon locations
icon_base_path = os.path.join(PATH, "resources")
icon_paths = {
    "play": os.path.join(icon_base_path, "play.png"),
    "pause": os.path.join(icon_base_path, "pause.png"),
    "back": os.path.join(icon_base_path, "back.png"),
    "forward": os.path.join(icon_base_path, "forward.png"),
    "restart": os.path.join(icon_base_path, "restart.png")
}

# Binary Waterfall abstraction class
#   Provides an abstract object for converting binary files
#   into audio files and image frames. This object does not
#   track time or handle playback, it only provides resources
#   to other code in order to produce the videos
class BinaryWaterfall:
    def __init__(self,
        filename,
        width=48,
        height=48,
        color_format_string="bgrx",
        num_channels=1,
        sample_bytes=1,
        sample_rate=32000,
        volume=100
    ):
        self.set_filename(
            filename=filename
        )
        
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
        try:
            os.remove(self.audio_filename)
        except FileNotFoundError:
            pass
    
    def compute_audio(self):
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
        self.setWindowTitle("Binary Waterfall")
        
        self.player_label = QLabel(self)
        self.player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.main_layout = QGridLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(20)
        
        self.main_layout.addWidget(self.player_label, 0, 0)
        
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        
        self.player = Player(self.player_label)
    
    #TODO: Add player area
    #TODO: Add menu, option to load a file
    #TODO: Add transport control buttons
    #TODO: Play audio and sync the image to the audio
    

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
    
    def scale_image(self, image):
        return image.resize(self.dim, Image.NEAREST)
    
    def set_image(self, image):
        self.image = self.scale_image(image).convert("RGBA")
        
        # Compute the QPixmap version
        qimage = ImageQt(self.image)
        qpixmap = QPixmap.fromImage(qimage)
        
        # Set the picture
        self.label.setPixmap(qpixmap)

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
        description="An audio-visual viewer for raw binary files.\n\nDefault parameters are shown in [brackets].",
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
