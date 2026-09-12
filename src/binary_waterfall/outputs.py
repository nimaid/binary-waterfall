import os
import shutil
import math
import threading
import tempfile
import pydub
from moviepy.editor import ImageSequenceClip, AudioFileClip
from PIL import Image
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
import numpy as np

from . import generators, helpers, constants, buffer_player


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

        self._audio_index = 0
        self._audio_lock = threading.Lock()
        self._playback_finished = False

        self.audio = buffer_player.BufferPlayer(
            self.obtain_data,
            samplerate=self.bw.sample_rate,
            channels=self.bw.num_channels,
        )

        # Set audio playback settings
        self.set_volume(100)

        self.fps_min = 1
        self.fps_max = 120
        self._ui_timer = QTimer(self.display)
        self._ui_timer.timeout.connect(self._on_playback_tick)
        self.set_fps(fps)

    def __del__(self):
        self.audio.close()

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
        self._ui_timer.setInterval(self.frame_ms)

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
        if self.bw.file is None:
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
        with self._audio_lock:
            frame = self._audio_index
        if self.bw.sample_rate <= 0:
            return 0
        return int(frame * 1000 / self.bw.sample_rate)

    def get_duration(self):
        return self.bw.get_audio_length_ms()

    def set_position(self, ms):
        duration = self.get_duration()

        ms = math.ceil(ms)
        if ms < 0:
            ms = 0
        if ms > duration:
            ms = duration

        with self._audio_lock:
            self._audio_index = self._ms_to_frame(ms)
            self._playback_finished = (
                duration > 0 and self._audio_index >= self._frame_count()
            )

        if self.bw.file is not None:
            self.set_image_timestamp(ms)
            self.set_seekbar_if_given(ms)

        if duration > 0 and ms >= duration:
            self.pause()

    def set_playbutton_if_given(self, play):
        if self.set_play_button is not None:
            self.set_play_button(play=play)

    def set_seekbar_if_given(self, ms):
        if self.set_seekbar_function is not None:
            self.set_seekbar_function(ms)

    def _on_playback_tick(self):
        if self._playback_finished:
            duration = self.get_duration()
            self.pause()
            self.set_position(duration)
            return

        ms = self.get_position()
        self.set_image_timestamp(ms)
        self.set_seekbar_if_given(ms)

    def play(self):
        if self.bw.file is None:
            return

        duration = self.get_duration()
        if duration > 0 and self.get_position() >= duration:
            self.set_position(0)

        with self._audio_lock:
            self._playback_finished = False

        self.audio.start()
        self._ui_timer.start()
        self.set_playbutton_if_given(play=False)
        self._on_playback_tick()

    def pause(self):
        self._ui_timer.stop()
        self.audio.stop()
        self.set_playbutton_if_given(play=True)

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

    def _sync_audio_stream(self):
        self.audio.update_stream_safe(
            sample_rate=self.bw.sample_rate,
            num_channels=self.bw.num_channels,
        )

    def open_file(self, filename):
        self.close_file()

        self.bw.change_filename(filename)
        self._sync_audio_stream()

        with self._audio_lock:
            self._audio_index = 0
            self._playback_finished = False

        self.set_image_timestamp(self.get_position())
        self.set_seekbar_if_given(self.get_position())
        self.set_playbutton_if_given(play=True)

    def close_file(self):
        self.pause()

        with self._audio_lock:
            self._audio_index = 0
            self._playback_finished = False

        self.bw.change_filename(None)

        self.set_seekbar_if_given(0)
        self.clear_image()

    def file_is_open(self):
        if self.bw.file is None:
            return False
        else:
            return True

    def is_playing(self):
        return self.audio.is_playing

    def set_image_timestamp(self, ms):
        if self.bw.file is None:
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
        was_playing = self.is_playing()
        ms = self.get_position()

        self.pause()

        self.bw.set_audio_settings(
            num_channels=num_channels,
            sample_bytes=sample_bytes,
            sample_rate=sample_rate,
            volume=volume
        )
        self._sync_audio_stream()
        self.set_position(ms)

        if was_playing:
            self.play()

    def obtain_data(self, n_frames):
        sample_bytes = self.bw.sample_bytes
        num_channels = self.bw.num_channels
        bytes_per_frame = sample_bytes * num_channels

        with self._audio_lock:
            if self.bw.file is None or bytes_per_frame <= 0:
                self._playback_finished = True
                return None

            byte_start = self._audio_index * bytes_per_frame
            if byte_start >= self.bw.get_total_bytes():
                self._playback_finished = True
                return None

            chunk_bytes = self.bw.get_file_bytes(byte_start, n_frames * bytes_per_frame)
            frames_read = len(chunk_bytes) // bytes_per_frame
            self._audio_index += frames_read
            if frames_read < n_frames:
                self._playback_finished = True

        chunk = buffer_player.pcm_bytes_to_float32(
            chunk_bytes,
            sample_bytes=sample_bytes,
            num_channels=num_channels,
        )

        if self.bw.volume != 100:
            chunk = chunk * np.float32(self.bw.volume / 100.0)
            np.clip(chunk, -1.0, 1.0, out=chunk)

        if frames_read < n_frames:
            pad = np.zeros((n_frames - frames_read, num_channels), dtype=np.float32)
            if frames_read == 0:
                chunk = pad
            else:
                chunk = np.vstack([chunk, pad])

        return chunk

    def _frame_count(self):
        if self.bw.file is None:
            return 0
        bytes_per_frame = self.bw.sample_bytes * self.bw.num_channels
        if bytes_per_frame <= 0:
            return 0
        return self.bw.get_total_bytes() // bytes_per_frame

    def _ms_to_frame(self, ms):
        if self.bw.sample_rate <= 0:
            return 0
        frame = int(round((ms / 1000) * self.bw.sample_rate))
        return min(max(frame, 0), self._frame_count())


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

        if self.bw.file is None:
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
                output_size = helpers.get_size_for_fit_frame(content_size=source.size, frame_size=size)["size"]
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
            self.bw.write_wav(filename)
            return

        wav_file = filename + ".temp.wav"
        try:
            self.bw.write_wav(wav_file)
            if filename_ext == constants.AudioFormatCode.MP3.value:
                pydub.AudioSegment.from_wav(wav_file).export(filename, format="mp3")
            elif filename_ext == constants.AudioFormatCode.FLAC.value:
                pydub.AudioSegment.from_wav(wav_file).export(filename, format="flac")
        finally:
            if os.path.isfile(wav_file):
                os.remove(wav_file)

    def get_frame_count(self, fps):
        audio_duration = self.bw.get_audio_length_ms() / 1000
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
            frame_filename = os.path.join(directory, f"{frame_number}{image_format.value}")
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
            progress_dialog.setLabelText("Splicing final video file... (program may lag)")

        # Export audio
        self.export_audio(audio_file)

        # Prepare the custom logger to update the progress box
        if progress_dialog is not None:
            custom_logger = helpers.QtBarLoggerMoviepy(progress_dialog=progress_dialog)
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
