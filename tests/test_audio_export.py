"""Run with QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests.

Integration checks require FFmpeg/ffprobe and the project's MoviePy 1.x API.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
import wave

from PIL import Image
from PyQt5.QtWidgets import QApplication

from binary_waterfall import constants, dialogs, outputs


class AudioChoicesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_container_choices(self):
        for container, expected in (
            (constants.VideoFormatCode.MP4, ["libmp3lame", "aac"]),
            (constants.VideoFormatCode.AVI,
             ["libmp3lame", "aac", "pcm_s16le", "pcm_s32le"]),
        ):
            with self.subTest(container=container):
                dialog = dialogs.VideoEncoderSettings(container)
                self.assertEqual(dialog.audio_codec_entry.count(), len(expected))
                for index, codec in enumerate(expected):
                    dialog.audio_codec_entry.setCurrentIndex(index)
                    self.assertEqual(dialog.get_settings()["audio_codec"].value, codec)
                dialog.close()

    def test_mp4_rejects_pcm_before_rendering(self):
        for codec in ("pcm_s16le", "pcm_s32le"):
            with self.subTest(codec=codec):
                with self.assertRaisesRegex(ValueError, "export as AVI"):
                    outputs.Renderer(None).export_video("video.MP4", 4, audio_codec=codec)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "FFmpeg and ffprobe are required")
class AudioExportIntegrationTest(unittest.TestCase):
    def test_video_audio_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.wav"
            with wave.open(str(source), "wb") as audio:
                audio.setparams((1, 2, 44100, 0, "NONE", "not compressed"))
                audio.writeframes(b"\x00\x10" * 22050)
            renderer = outputs.Renderer(SimpleNamespace(
                audio_filename=str(source),
                get_audio_length=lambda: 500,
                get_frame_image=lambda ms: Image.new("RGB", (16, 16), "red"),
            ))
            for extension, video_codec, audio_codec, expected in (
                ("mp4", "libx264", constants.AudioCodecCode.M4A.value, "aac"),
                ("mp4", "libx264", "libmp3lame", "mp3"),
                ("avi", "png", constants.AudioCodecCode.M4A.value, "aac"),
                ("avi", "png", "pcm_s16le", "pcm_s16le"),
                ("avi", "png", "pcm_s32le", "pcm_s32le"),
            ):
                with self.subTest(container=extension, codec=audio_codec):
                    target = Path(directory) / f"{audio_codec}.{extension}"
                    renderer.export_video(str(target), 4, codec=video_codec,
                                          audio_codec=audio_codec, preset="ultrafast")
                    probe = subprocess.run(
                        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(target)],
                        check=True, capture_output=True, text=True,
                    )
                    streams = json.loads(probe.stdout)["streams"]
                    audio = next(s for s in streams if s["codec_type"] == "audio")
                    self.assertEqual(audio["codec_name"], expected)
                    self.assertGreater(int(audio["sample_rate"]), 0)
                    subprocess.run(["ffmpeg", "-v", "error", "-i", str(target),
                                    "-f", "null", "-"], check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
