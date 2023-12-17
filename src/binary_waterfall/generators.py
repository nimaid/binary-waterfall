import os
import shutil
import tempfile
import math
import wave
from PIL import Image, ImageOps
import pydub
from PyQt5.QtGui import QImage

from . import constants, helpers


# Binary Waterfall abstraction class
#   Provides an abstract object for converting binary files
#   into audio files and image frames. This object does not
#   track time or handle playback, it only provides resources
#   to other code in order to produce the videos
class BinaryWaterfall:
    def __init__(self,
                 filename=None,
                 width=constants.DEFAULTS["width"],
                 height=constants.DEFAULTS["height"],
                 color_format_string=constants.DEFAULTS["color_format_string"],
                 num_channels=constants.DEFAULTS["num_channels"],
                 sample_bytes=constants.DEFAULTS["sample_bytes"],
                 sample_rate=constants.DEFAULTS["sample_rate"],
                 volume=constants.DEFAULTS["volume"],
                 flip_v=constants.DEFAULTS["flip_v"],
                 flip_h=constants.DEFAULTS["flip_h"],
                 alignment=constants.DEFAULTS["alignment"]
                 ):
        # Initialize class variables
        self.audio_length_ms = None
        self.volume = None
        self.sample_rate = None
        self.sample_bytes = None
        self.num_channels = None
        self.color_format = None
        self.color_bytes = None
        self.unused_color_bytes = None
        self.used_color_bytes = None
        self.filename = None
        self.height = None
        self.width = None
        self.dim = None
        self.total_bytes = None
        self.file = None
        self.audio_filename = None
        self.flip_v = None
        self.flip_h = None
        self.alignment = alignment

        # Make the temp dir for the class instance
        self.temp_dir = tempfile.mkdtemp()

        # Set the filename in
        self.set_filename(filename=filename)

        # Set the dims in
        self.set_dims(
            width=width,
            height=height
        )

        self.set_color_format(color_format_string=color_format_string)

        self.set_flip(
            flip_v=flip_v,
            flip_h=flip_h
        )

        self.set_alignment(alignment=alignment)

        self.set_audio_settings(
            num_channels=num_channels,
            sample_bytes=sample_bytes,
            sample_rate=sample_rate,
            volume=volume
        )

    def __del__(self):
        self.cleanup()

    def close_file(self):
        if self.file is not None:
            self.file.close()
            self.file = None
        self.filename = None

    def set_filename(self, filename):
        # Delete current audio file if it exists
        self.delete_audio()

        if filename is None:
            # Reset all vars and close the file pointer
            self.close_file()
            self.total_bytes = None
            self.audio_filename = None
            return

        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: \"{filename}\"")

        self.filename = os.path.realpath(filename)

        # Open file
        self.file = open(self.filename, "rb")

        # Get total number of bytes
        self.file.seek(0, os.SEEK_END)
        self.total_bytes = self.file.tell()
        self.file.seek(0)

        # Compute audio file name
        file_path, file_main_name = os.path.split(self.filename)
        self.audio_filename = os.path.join(
            self.temp_dir,
            file_main_name + os.path.extsep + "wav"
        )

    def set_dims(self, width, height):
        if width < 4:
            raise ValueError("Visualization width must be at least 4")

        if height < 4:
            raise ValueError("Visualization height must be at least 4")

        self.width = width
        self.height = height
        self.dim = (self.width, self.height)

    @staticmethod
    def parse_color_format(color_format_string):
        result = {
            "is_valid": True
        }

        color_format_string = color_format_string.strip()
        lower_string = color_format_string.lower()

        format_code_groups = {
            "red": f"{{{constants.ColorFmtCode.RED.value},{constants.ColorFmtCode.RED_INV.value}}}",
            "green": f"{{{constants.ColorFmtCode.GREEN.value},{constants.ColorFmtCode.GREEN_INV.value}}}",
            "blue": f"{{{constants.ColorFmtCode.BLUE.value},{constants.ColorFmtCode.BLUE_INV.value}}}",
            "white": f"{{{constants.ColorFmtCode.WHITE.value},{constants.ColorFmtCode.WHITE_INV.value}}}",
            "unused": f"{{{constants.ColorFmtCode.UNUSED.value}}}"
        }

        for c in color_format_string:
            if c not in [x.value for x in constants.ColorFmtCode]:
                result["is_valid"] = False
                result["message"] = ("Color channel formatting codes only accept \"{r}\" = red, \"{g}\" = green, "
                                     "\"{b}\" = blue, \"{w}\" = white, \"{u}\" = unused. To invert a color channel, "
                                     "CAPITALIZE the letter.").format(
                    r=constants.ColorFmtCode.RED.value,
                    g=constants.ColorFmtCode.GREEN.value,
                    b=constants.ColorFmtCode.BLUE.value,
                    w=constants.ColorFmtCode.WHITE.value,
                    u=constants.ColorFmtCode.UNUSED.value
                )
                return result

        red_count = lower_string.count(constants.ColorFmtCode.RED.value)
        green_count = lower_string.count(constants.ColorFmtCode.GREEN.value)
        blue_count = lower_string.count(constants.ColorFmtCode.BLUE.value)
        white_count = lower_string.count(constants.ColorFmtCode.WHITE.value)
        unused_count = lower_string.count(constants.ColorFmtCode.UNUSED.value)

        rgb_count = red_count + green_count + blue_count

        if white_count > 0:
            color_mode = constants.ColorModeCode.GRAYSCALE

            if rgb_count > 0:
                result["is_valid"] = False
                result["message"] = ("When using the grayscale mode formatter {w}, "
                                     "you cannot use any of the RGB mode formatters {r}, "
                                     "{g}, or {b}").format(
                    r=format_code_groups["red"],
                    g=format_code_groups["green"],
                    b=format_code_groups["blue"],
                    w=format_code_groups["white"]
                                  )
                return result

            if white_count > 1:
                result["is_valid"] = False
                result["message"] = ("Exactly 1 white channel format specifier {w} needed, "
                                     "but {white_count} were given in format string \"{color_format_string}\"").format(
                    w=format_code_groups["white"],
                    white_count=white_count,
                    color_format_string=color_format_string
                )
                return result
        else:
            color_mode = constants.ColorModeCode.RGB

            if rgb_count < 1:
                result["is_valid"] = False
                result["message"] = ("A minimum of 1 color format specifier ({r}, {g}, {b}, "
                                     "or {w}) is required, but none were given in format string "
                                     "\"{color_format_string}\"").format(
                    r=format_code_groups["red"],
                    g=format_code_groups["green"],
                    b=format_code_groups["blue"],
                    w=format_code_groups["white"],
                    color_format_string=color_format_string
                )
                return result

            if red_count > 1:
                result["is_valid"] = False
                result["message"] = ("Exactly 1 red channel format specifier {r} allowed, but {red_count} "
                                     "were given in format string \"{color_format_string}\"").format(
                    r=format_code_groups["red"],
                    red_count=red_count,
                    color_format_string=color_format_string
                )
                return result

            if green_count > 1:
                result["is_valid"] = False
                result["message"] = ("Exactly 1 green channel format specifier {g} allowed, but {green_count} "
                                     "were given in format string \"{color_format_string}\"").format(
                    g=format_code_groups["green"],
                    green_count=green_count,
                    color_format_string=color_format_string
                )
                return result

            if blue_count > 1:
                result["is_valid"] = False
                result["message"] = ("Exactly 1 blue channel format specifier {b} allowed, but {blue_count} "
                                     "were given in format string \"{color_format_string}\"").format(
                    b=format_code_groups["blue"],
                    blue_count=blue_count,
                    color_format_string=color_format_string
                )
                return result

        color_format_list = list()
        for c in color_format_string:
            color_format_list.append(constants.ColorFmtCode(c))

        result["used_color_bytes"] = rgb_count + white_count
        result["unused_color_bytes"] = unused_count
        result["color_bytes"] = result["used_color_bytes"] + result["unused_color_bytes"]
        result["color_mode"] = color_mode
        result["color_format"] = color_format_list

        return result

    def set_color_format(self, color_format_string):
        parsed_string = self.parse_color_format(color_format_string)

        if not parsed_string["is_valid"]:
            raise ValueError(parsed_string["message"])

        self.used_color_bytes = parsed_string["used_color_bytes"]
        self.unused_color_bytes = parsed_string["unused_color_bytes"]
        self.color_bytes = parsed_string["color_bytes"]
        self.color_format = parsed_string["color_format"]

    def get_color_format_string(self):
        color_format_string = ""
        for x in self.color_format:
            color_format_string += x.value

        return color_format_string

    def is_color_format_valid(self, color_format_string):
        return self.parse_color_format(color_format_string)["is_valid"]

    def set_flip(self, flip_v, flip_h):
        self.flip_v = flip_v
        self.flip_h = flip_h

    def set_alignment(self, alignment):
        self.alignment = alignment

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
        if self.audio_filename is None:
            # Do nothing
            return
        try:
            os.remove(self.audio_filename)
        except FileNotFoundError:
            pass

    def get_audio_length(self):
        audio_length = pydub.AudioSegment.from_file(self.audio_filename).duration_seconds
        audio_length_ms = math.ceil(audio_length * 1000)

        return audio_length_ms

    def compute_audio(self):
        if self.filename is None:
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
            self.file.seek(0)
            for chunk in iter(lambda: self.file.read(4096), b""):
                f.writeframesraw(chunk)

        if self.volume != 100:
            # Reduce the audio volume
            factor = self.volume / 100
            audio = pydub.AudioSegment.from_file(file=self.audio_filename, format="wav")
            audio += pydub.audio_segment.ratio_to_db(factor)
            temp_filename = self.audio_filename + ".temp"
            audio.export(temp_filename, format="wav")
            self.delete_audio()
            shutil.move(temp_filename, self.audio_filename)

        # Get audio length
        self.audio_length_ms = self.get_audio_length()

    def change_filename(self, new_filename):
        self.set_filename(new_filename)
        self.compute_audio()

    def get_file_bytes(self, address, count):
        self.file.seek(address)
        return self.file.read(count)

    def get_address(self, ms):
        # Get the size of a single "block" (a row, we only move in increments of 1 row)
        address_block_size = self.width * self.color_bytes

        # Get the total number of blocks (rows) in the file (round up because we don't want to clip a row off)
        total_blocks = math.ceil(self.total_bytes / address_block_size)

        # Get the block index of the current audio location
        address_block_index = round(total_blocks * (ms / self.audio_length_ms))

        # Adjust index for other alignments
        if self.alignment == constants.AlignmentCode.START:
            address_block_index -= self.height
        elif self.alignment == constants.AlignmentCode.MIDDLE:
            address_block_index -= round(self.height / 2)

        # Get the base address (end of frame by default)
        address = address_block_index * address_block_size

        return address

    # A 1D Python byte string
    def get_frame_bytestring(self, ms):
        picture_bytes = bytes()

        address = self.get_address(ms)
        # Compensate for negative addresses
        if address < 0:
            picture_bytes += b"\x00" * 3 * round(-address / self.color_bytes)
            address = 0

        # Get the maximum number of bytes that could be used for this frame
        frame_bytes = self.get_file_bytes(
            address=address,
            count=(self.width * self.height * self.color_bytes)
        )

        full_length = (self.width * self.height * 3)

        idx = 0
        for row in range(self.height):
            for col in range(self.width):
                # If we already have a full frame, stop the loops
                if len(picture_bytes) >= full_length:
                    break

                # Fill one BGR byte value
                this_byte = [b'\x00', b'\x00', b'\x00']
                for c in self.color_format:
                    if c == constants.ColorFmtCode.RED:
                        this_byte[0] = frame_bytes[idx:idx + 1]  # Red
                    elif c == constants.ColorFmtCode.RED_INV:
                        this_byte[0] = helpers.invert_bytes(frame_bytes[idx:idx + 1])  # Red inverted
                    elif c == constants.ColorFmtCode.GREEN:
                        this_byte[1] = frame_bytes[idx:idx + 1]  # Green
                    elif c == constants.ColorFmtCode.GREEN_INV:
                        this_byte[1] = helpers.invert_bytes(frame_bytes[idx:idx + 1])  # Green inverted
                    elif c == constants.ColorFmtCode.BLUE:
                        this_byte[2] = frame_bytes[idx:idx + 1]  # Blue
                    elif c == constants.ColorFmtCode.BLUE_INV:
                        this_byte[2] = helpers.invert_bytes(frame_bytes[idx:idx + 1])  # Blue inverted
                    elif c == constants.ColorFmtCode.WHITE:
                        this_byte[0] = frame_bytes[idx:idx + 1]  # Red
                        this_byte[1] = frame_bytes[idx:idx + 1]  # Green
                        this_byte[2] = frame_bytes[idx:idx + 1]  # Blue
                    elif c == constants.ColorFmtCode.WHITE_INV:
                        this_byte[0] = helpers.invert_bytes(frame_bytes[idx:idx + 1])  # Red inverted
                        this_byte[1] = helpers.invert_bytes(frame_bytes[idx:idx + 1])  # Green inverted
                        this_byte[2] = helpers.invert_bytes(frame_bytes[idx:idx + 1])  # Blue inverted

                    idx += 1

                picture_bytes += b"".join(this_byte)
            else:
                continue
            break

        # Pad picture data if we don't have a full frame (near the end of the file)
        picture_bytes_length = len(picture_bytes)
        if picture_bytes_length < full_length:
            pad_length = full_length - picture_bytes_length
            picture_bytes += b"\x00" * pad_length

        return picture_bytes

    # A PIL Image (RGB)
    def get_frame_image(self, ms):
        frame_bytesring = self.get_frame_bytestring(ms)
        img = Image.frombytes("RGB", (self.width, self.height), frame_bytesring)

        if self.flip_v:
            img = ImageOps.flip(img)
        if self.flip_h:
            img = ImageOps.mirror(img)

        return img

    # A QImage (RGB)
    def get_frame_qimage(self, ms):
        frame_bytesring = self.get_frame_bytestring(ms)
        qimg = QImage(
            frame_bytesring,
            self.width,
            self.height,
            3 * self.width,
            QImage.Format.Format_RGB888
        )
        if self.flip_v or self.flip_h:
            # Flip vertically
            qimg = qimg.mirrored(horizontal=self.flip_h, vertical=self.flip_v)

        return qimg

    def cleanup(self):
        self.close_file()
        self.delete_audio()
        shutil.rmtree(self.temp_dir)


# Watermarker class
#   Handles watermarking images
class Watermarker:
    def __init__(self):
        self.img = Image.open(constants.ICON_PATHS["watermark"]).convert("RGBA")

    def mark(self, image):
        this_mark = self.img.copy()
        this_mark = helpers.fit_to_frame(
            image=this_mark,
            frame_size=image.size,
            scaling=Image.BICUBIC,
            transparent=True
        )

        output_image = image.copy()
        output_image.paste(this_mark, (0, 0), this_mark)

        return output_image
