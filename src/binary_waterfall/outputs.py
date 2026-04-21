import os
import shutil
import math
import time
import tempfile
import pydub
# moviepy 2.x exposes core classes at package root; import directly for compatibility
from moviepy import ImageSequenceClip, AudioFileClip
from PIL import Image
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QImage, QPixmap

from . import generators, helpers, constants


# Image playback class
#   Provides an abstraction for displaying images and audio in the GUI
class Player:
    def __init__(self,
                 binary_waterfall,
                 display,
                 set_playbutton_function=None,
                 set_seekbar_function=None,
                 max_dim=constants.DEFAULTS["max_dim"],
                 fps=constants.DEFAULTS["player_fps"]
                 ):
        self.image = None
        self.volume = None
        self.fps = None
        self.frame_ms = None
        self.height = None
        self.width = None
        self.dim = None
        self.max_dim = None

        self.bw = binary_waterfall

        self.display = display

        self.set_dims(max_dim=max_dim)

        self.set_play_button = set_playbutton_function
        self.set_seekbar_function = set_seekbar_function

        # Initialize player as black
        self.clear_image()

        # Make the QMediaPlayer for audio playback
        self.audio = QMediaPlayer()
        # self.audio_output = QAudioOutput()
        # self.audio.setAudioOutput(self.audio_output)

        # Set audio playback settings
        self.set_volume(100)

        # Set set_image_timestamp to run when the audio position is changed
        self.audio.positionChanged.connect(self.set_image_timestamp)
        self.audio.positionChanged.connect(self.set_seekbar_if_given)
        # Also, make sure it's updating more frequently (default is too slow when playing)
        self.fps_min = 1
        self.fps_max = 120
        self.set_fps(fps)

        # Setup change state handler
        self.audio.stateChanged.connect(self.state_changed_handler)

    def __del__(self):
        self.running = False

    def set_dims(self, max_dim):
        self.max_dim = max_dim
        if self.bw.width > self.bw.height:
            self.width = round(max_dim)
            self.height = round(self.width * (self.bw.height / self.bw.width))
        else:
            self.height = round(max_dim)
            self.width = round(self.height * (self.bw.width / self.bw.height))

        self.dim = (self.width, self.height)

    def set_fps(self, fps):
        self.fps = min(max(fps, self.fps_min), self.fps_max)
        self.frame_ms = math.floor(1000 / self.fps)
        self.audio.setNotifyInterval(self.frame_ms)

    def clear_image(self):
        background_image = Image.new(
            mode="RGBA",
            size=(self.width, self.height),
            color=constants.COLORS["viewer"]
        )

        background_image = generators.Watermarker().mark(background_image)

        img_bytestring = background_image.convert("RGB").tobytes()

        qimg = QImage(
            img_bytestring,
            self.width,
            self.height,
            3 * self.width,
            QImage.Format.Format_RGB888
        )

        self.set_image(qimg)

    def update_dims(self, max_dim):
        # Change dims
        self.set_dims(max_dim=max_dim)

        # Update image
        if self.bw.filename is None:
            self.clear_image()
        else:
            self.set_image(self.image)

    def refresh_dims(self):
        self.update_dims(self.max_dim)

    def set_volume(self, volume):
        self.volume = volume
        self.audio.setVolume(volume)

    def scale_image(self, image):
        return image.scaled(self.width, self.height)

    def set_image(self, image):
        self.image = self.scale_image(image)

        # Compute the QPixmap version
        qpixmap = QPixmap.fromImage(self.image)

        # Set the picture
        self.display.setPixmap(qpixmap)

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

        if self.bw.filename is not None:
            self.audio.setPosition(ms)

        # If the file is at the end, pause
        if ms == duration:
            self.pause()

    def set_playbutton_if_given(self, play):
        if self.set_play_button is not None:
            self.set_play_button(play=play)

    def set_seekbar_if_given(self, ms):
        if self.set_seekbar_function is not None:
            self.set_seekbar_function(ms)

    def state_changed_handler(self, media_state):
        if media_state == self.audio.PlayingState:
            self.set_playbutton_if_given(play=False)
        elif media_state == self.audio.PausedState:
            self.set_playbutton_if_given(play=True)
        elif media_state == self.audio.StoppedState:
            self.set_playbutton_if_given(play=True)

    def play(self):
        self.audio.play()

    def pause(self):
        self.audio.pause()

    def forward(self, ms=5000):
        new_pos = self.get_position() + ms
        self.set_position(new_pos)

    def back(self, ms=5000):
        new_pos = self.get_position() - ms
        self.set_position(new_pos)

    def frame_forward(self):
        self.forward(ms=self.frame_ms)

    def frame_back(self):
        self.back(ms=self.frame_ms)

    def restart(self):
        self.set_position(0)

    def set_audio_file(self, filename):
        if filename is None:
            url = QUrl(None)
        else:
            url = QUrl.fromLocalFile(self.bw.audio_filename)
        media = QMediaContent(url)
        self.audio.setMedia(media)

    def open_file(self, filename):
        self.close_file()

        self.bw.change_filename(filename)

        self.set_audio_file(self.bw.audio_filename)

        self.set_image_timestamp(self.get_position())

    def close_file(self):
        self.pause()

        self.audio.stop()
        time.sleep(0.001)  # Without a short delay here, we crash
        self.set_audio_file(None)

        self.bw.change_filename(None)

        self.restart()
        self.clear_image()

    def file_is_open(self):
        if self.bw.filename is None:
            return False
        else:
            return True

    def is_playing(self):
        if self.audio.state() == self.audio.PlayingState:
            return True
        else:
            return False

    def set_image_timestamp(self, ms):
        if self.bw.filename is None:
            self.clear_image()
        else:
            self.set_image(self.bw.get_frame_qimage(ms))

    def update_image(self):
        ms = self.get_position()
        self.set_image_timestamp(ms)

    def set_audio_settings(self,
                           num_channels,
                           sample_bytes,
                           sample_rate,
                           volume
                           ):
        self.bw.set_audio_settings(
            num_channels=num_channels,
            sample_bytes=sample_bytes,
            sample_rate=sample_rate,
            volume=volume
        )
        # Re-open newly computed file
        self.set_audio_file(None)
        self.set_audio_file(self.bw.audio_filename)


# Renderer class
#   Provides an abstraction for rendering images, audio, and video to files
class Renderer:
    def __init__(self,
                 binary_waterfall,
                 ):
        self.bw = binary_waterfall

    def export_frame(self,
                     ms,
                     filename,
                     size=None,
                     keep_aspect=False
                     ):
        helpers.make_file_path(filename)

        if self.bw.audio_filename is None:
            # If no file is loaded, make a black image
            source = Image.new(
                mode="RGBA",
                size=(self.bw.width, self.bw.height),
                color="#000"
            )
        else:
            source = self.bw.get_frame_image(ms).convert("RGBA")

        # Resize with aspect ratio, paste onto black
        if size is None:
            resized = source
        else:
            if keep_aspect:
                output_size = helpers.get_size_for_fit_frame(
                    content_size=source.size, frame_size=size)["size"]
            else:
                output_size = size

            resized = helpers.fit_to_frame(
                image=source,
                frame_size=output_size,
                scaling=Image.NEAREST,
                transparent=False
            )

        final = resized.convert("RGB")

        final.save(filename)

    def export_audio(self, filename):
        filename_main, filename_ext = os.path.splitext(filename)
        filename_ext = filename_ext.lower()

        helpers.make_file_path(filename)

        if filename_ext == constants.AudioFormatCode.WAVE.value:
            # Just copy the .wav file
            shutil.copy(self.bw.audio_filename, filename)
        elif filename_ext == constants.AudioFormatCode.MP3.value:
            # Use Pydub to export MP3
            pydub.AudioSegment.from_wav(
                self.bw.audio_filename).export(filename, format="mp3")
        elif filename_ext == constants.AudioFormatCode.FLAC.value:
            # Use Pydub to export FLAC
            pydub.AudioSegment.from_wav(
                self.bw.audio_filename).export(filename, format="flac")

    def get_frame_count(self, fps):
        audio_duration = self.bw.get_audio_length() / 1000
        frame_count = round(audio_duration * fps)

        return frame_count

    def export_sequence(self,
                        directory,
                        fps,
                        size=None,
                        keep_aspect=False,
                        image_format=None,
                        progress_dialog=None
                        ):
        helpers.make_file_path(directory)

        frame_count = self.get_frame_count(fps)

        frame_number_digits = len(str(frame_count))

        if image_format is None:
            image_format = constants.ImageFormatCode.PNG

        for frame in range(frame_count):
            frame_number = str(frame).rjust(frame_number_digits, "0")
            frame_filename = os.path.join(
                directory, f"{frame_number}{image_format.value}")
            frame_ms = round((frame / fps) * 1000)

            if progress_dialog is not None:
                progress_dialog.setValue(frame)

                if progress_dialog.wasCanceled():
                    return

            self.export_frame(
                ms=frame_ms,
                filename=frame_filename,
                size=size,
                keep_aspect=keep_aspect
            )

        if progress_dialog is not None:
            progress_dialog.setValue(frame_count)

    def export_video(self,
                     filename,
                     fps,
                     size=None,
                     keep_aspect=False,
                     progress_dialog=None,
                     codec=None,
                     audio_codec=None,
                     bitrate=None,
                     audio_bitrate=None,
                     preset=None
                     ):
        # Get temporary directory
        temp_dir = tempfile.mkdtemp()

        # Make file names
        image_dir = os.path.join(temp_dir, "images")
        audio_file = os.path.join(temp_dir, "audio.wav")
        filename_main, filename_ext = os.path.splitext(filename)
        filename_path, filename_title = os.path.split(filename)
        video_file = os.path.join(temp_dir, f"video{filename_ext}")

        # Set progress dialog to not close when at max
        if progress_dialog is not None:
            progress_dialog.setAutoReset(False)

        # Export image sequence
        self.export_sequence(
            directory=image_dir,
            fps=fps,
            size=size,
            keep_aspect=keep_aspect,
            image_format=constants.ImageFormatCode.PNG,
            progress_dialog=progress_dialog
        )

        if progress_dialog is not None:
            if progress_dialog.wasCanceled():
                shutil.rmtree(temp_dir)
                return
            progress_dialog.setLabelText(
                "Splicing final video file... (program may lag)")

        # Export audio
        self.export_audio(audio_file)

        # Prepare the custom logger to update the progress box
        if progress_dialog is not None:
            custom_logger = helpers.QtBarLoggerMoviepy(
                progress_dialog=progress_dialog)
        else:
            custom_logger = "bar"

        # Make a list of the image filenames
        frames_list = list()
        for frame_filename in os.listdir(image_dir):
            full_frame_filename = os.path.join(image_dir, frame_filename)
            frames_list.append(full_frame_filename)

        # Merge image sequence and audio into final video
        sequence_clip = ImageSequenceClip(frames_list, fps=fps)
        audio_clip = AudioFileClip(audio_file)

        video_clip = sequence_clip.set_audio(audio_clip)
        # TODO: Control quality settings
        # TODO: Set temp audio file location if possible
        video_clip.write_videofile(
            filename=video_file,
            codec=codec,
            bitrate=bitrate,
            audio_codec=audio_codec,
            audio_bitrate=audio_bitrate,
            preset=preset,
            threads=None,
            logger=custom_logger,
            temp_audiofile=None
        )

        if progress_dialog is not None:
            if progress_dialog.wasCanceled():
                shutil.rmtree(temp_dir)
                return

            # Reset progress dialog and set to exit on completion
            progress_dialog.setLabelText("Wrapping up...")
            progress_dialog.setValue(0)
            progress_dialog.setMaximum(100)
            progress_dialog.setAutoReset(True)

        # Move video to final location
        os.makedirs(filename_path, exist_ok=True)
        shutil.move(video_file, filename)

        # Delete temporary files
        shutil.rmtree(temp_dir)

        if progress_dialog is not None:
            progress_dialog.setValue(100)
