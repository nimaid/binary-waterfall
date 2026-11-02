import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "src/binary_waterfall/reversible_video.py"

spec = importlib.util.spec_from_file_location(
    "reversible_video_under_test", MODULE_PATH
)
reversible_video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reversible_video)


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "FFmpeg and FFprobe are required",
)
class ReversibleRoundTripTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_exact_recovery_at_frame_boundaries(self):
        sizes = [
            0, 1, 63, 64,
            196543, 196544, 196545,
            196608, 196609,
            1048609,
        ]

        for size in sizes:
            with self.subTest(size=size):
                source = self.folder / "original.bin"
                video = self.folder / "recovery.mkv"
                restored = self.folder / "restored.bin"

                source.write_bytes(
                    bytes(range(256)) * (size // 256)
                    + bytes(range(size % 256))
                )

                video.unlink(missing_ok=True)
                restored.unlink(missing_ok=True)

                reversible_video.encode(source, video)
                reversible_video.decode(video, restored)

                self.assertEqual(
                    source.read_bytes(), restored.read_bytes()
                )

    def test_no_implicit_overwrite(self):
        source = self.folder / "input.bin"
        video = self.folder / "output.mkv"
        destination = self.folder / "restored.bin"

        source.write_bytes(b"Binary Waterfall test data")
        video.write_bytes(b"existing video")

        with self.assertRaises(Exception):
            reversible_video.encode(source, video)

        self.assertEqual(video.read_bytes(), b"existing video")

        video.unlink()
        reversible_video.encode(source, video)

        destination.write_bytes(b"existing destination")

        with self.assertRaises(Exception):
            reversible_video.decode(video, destination)

        self.assertEqual(
            destination.read_bytes(), b"existing destination"
        )

    def test_reject_video_without_recovery_stream(self):
        video = self.folder / "ordinary.mkv"
        destination = self.folder / "should-not-exist.bin"

        subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-nostdin", "-y",
            "-f", "lavfi", "-i",
            "color=c=black:s=256x256:r=1:d=1",
            "-c:v", "libx264",
            str(video),
        ], check=True, capture_output=True)

        with self.assertRaises(Exception):
            reversible_video.decode(video, destination)

        self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
