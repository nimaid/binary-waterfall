import tempfile
import unittest
import wave
from pathlib import Path

from binary_waterfall.audio_endianness import convert_pcm_byte_order
from binary_waterfall.generators import BinaryWaterfall


class TestAudioEndianness(unittest.TestCase):

    def test_sample_widths(self):
        for width in (1, 2, 3, 4):
            with self.subTest(width=width):
                source = bytes(range(1, width + 1))
                expected = source if width == 1 else source[::-1]
                actual, remainder = convert_pcm_byte_order(
                    source, width, "big"
                )
                self.assertEqual(actual, expected)
                self.assertEqual(remainder, b"")

    def test_little_endian_unchanged(self):
        data = bytes.fromhex("123456789abc")
        actual, remainder = convert_pcm_byte_order(
            data, 2, "little"
        )
        self.assertEqual(actual, data)
        self.assertEqual(remainder, b"")

    def test_incomplete_sample(self):
        actual, remainder = convert_pcm_byte_order(
            bytes.fromhex("123456789a"), 3, "big"
        )
        self.assertEqual(actual, bytes.fromhex("563412"))
        self.assertEqual(remainder, bytes.fromhex("789a"))

    def test_invalid_settings(self):
        for width, order in ((0, "big"), (5, "big"), (2, "invalid")):
            with self.subTest(width=width, order=order):
                with self.assertRaises(ValueError):
                    convert_pcm_byte_order(b"1234", width, order)

    def test_generated_wav_all_widths(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "test.raw"

            for width in (1, 2, 3, 4):
                with self.subTest(width=width):
                    # Cross the generator's 4096-byte chunk boundary.
                    samples = [
                        bytes((i + j) % 256 for j in range(width))
                        for i in range(4100 // width + 1)
                    ]
                    raw = b"".join(samples)
                    source.write_bytes(raw)

                    bw = BinaryWaterfall(
                        filename=str(source),
                        num_channels=1,
                        sample_bytes=width,
                        sample_rate=8000,
                        volume=100,
                        byte_order="big",
                    )

                    try:
                        with wave.open(bw.audio_filename, "rb") as wav:
                            actual = wav.readframes(wav.getnframes())

                        expected = b"".join(
                            sample[::-1] for sample in samples
                        )
                        self.assertEqual(actual, expected)
                    finally:
                        bw.close_file()

    def test_incomplete_final_24_bit_sample(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "test.raw"
            source.write_bytes(bytes.fromhex("123456789a"))

            bw = BinaryWaterfall(
                filename=str(source),
                num_channels=1,
                sample_bytes=3,
                sample_rate=8000,
                volume=100,
                byte_order="big",
            )

            try:
                with wave.open(bw.audio_filename, "rb") as wav:
                    actual = wav.readframes(wav.getnframes())

                # The final incomplete sample is zero-padded.
                self.assertEqual(
                    actual, bytes.fromhex("563412009a78")
                )
            finally:
                bw.close_file()


if __name__ == "__main__":
    unittest.main()
