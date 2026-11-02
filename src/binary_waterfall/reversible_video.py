"""Lossless reversible binary-to-video conversion using FFV1."""

import argparse
import hashlib
import json
import os
import struct
import subprocess
import tempfile
import threading
from pathlib import Path

MAGIC = b"BWREV001"
WIDTH = HEIGHT = 256
FRAME_SIZE = WIDTH * HEIGHT * 3
HEADER_SIZE = 64
CHUNK_SIZE = 1024 * 1024


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for chunk in iter(lambda: source.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.digest()


def ffmpeg_command(*args):
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error",
        "-nostdin", *args
    ]


def encode(source, destination, overwrite=False):
    source = Path(source).resolve()
    destination = Path(destination).resolve()

    if source == destination:
        raise ValueError("Input and output must differ")

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {destination}"
        )

    size = source.stat().st_size
    digest = file_hash(source)

    header = struct.pack("<8sQ32s", MAGIC, size, digest)
    header += bytes(HEADER_SIZE - len(header))

    # Encode to a temporary MKV before publishing.
    with tempfile.NamedTemporaryFile(
        suffix=".mkv",
        prefix=".bw-export-",
        dir=destination.parent,
        delete=False,
    ) as temp:
        temp_path = Path(temp.name)

    command = ffmpeg_command(
        "-f", "rawvideo",
        "-pixel_format", "rgb24",
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", "1",
        "-i", "pipe:0",
        "-an",
        "-c:v", "ffv1",
        "-level", "3",
        "-pix_fmt", "gbrp",
        "-y", str(temp_path)
    )

    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE
    )

    errors = bytearray()

    def drain_errors():
        for chunk in iter(lambda: proc.stderr.read(4096), b""):
            errors.extend(chunk)

    reader = threading.Thread(target=drain_errors, daemon=True)
    reader.start()

    try:
        written = 0

        def write(data):
            nonlocal written
            proc.stdin.write(data)
            written += len(data)

        write(header)

        with source.open("rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                write(chunk)

        padding = (-written) % FRAME_SIZE

        if padding:
            # Use bounded writes instead of allocating large padding.
            while padding:
                count = min(padding, 65536)
                write(bytes(count))
                padding -= count

        proc.stdin.close()
        returncode = proc.wait()
        reader.join()

        if returncode:
            raise RuntimeError(
                errors.decode(errors="replace")
                or "FFmpeg encoding failed"
            )

    except Exception:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        reader.join()
        temp_path.unlink(missing_ok=True)
        raise

    finally:
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None and not stream.closed:
                stream.close()

    try:
        if destination.exists() and not overwrite:
            raise FileExistsError(destination)
        os.replace(temp_path, destination)
    finally:
        temp_path.unlink(missing_ok=True)

    print(f"Encoded {size} bytes to {destination}")
    print(f"SHA-256: {digest.hex()}")



def find_recovery_stream(source):
    """Find a compatible FFV1 recovery stream in a video."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "stream=index,codec_name,codec_type,width,height",
            "-of", "json", str(source),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    streams = json.loads(result.stdout).get("streams", [])

    candidates = [
        stream["index"]
        for stream in streams
        if stream.get("codec_type") == "video"
        and stream.get("codec_name") == "ffv1"
        and stream.get("width") == WIDTH
        and stream.get("height") == HEIGHT
    ]

    if not candidates:
        raise ValueError("No compatible FFV1 recovery stream found")

    if len(candidates) > 1:
        raise ValueError("Multiple recovery streams found")

    return candidates[0]


def decode(source, destination, overwrite=False):
    source = Path(source).resolve()
    destination = Path(destination).resolve()

    if source == destination:
        raise ValueError("Input and output must differ")

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {destination}"
        )

    stream_index = find_recovery_stream(source)

    command = ffmpeg_command(
        "-i", str(source),
        "-map", f"0:{stream_index}",
        "-f", "rawvideo",
        "-pix_fmt", "rgb24",
        "pipe:1"
    )

    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    errors = bytearray()

    def drain_errors():
        for chunk in iter(lambda: proc.stderr.read(4096), b""):
            errors.extend(chunk)

    reader = threading.Thread(target=drain_errors, daemon=True)
    reader.start()

    temp_path = None

    try:
        header = bytearray()

        while len(header) < HEADER_SIZE:
            chunk = proc.stdout.read(HEADER_SIZE - len(header))
            if not chunk:
                raise ValueError("Incomplete reversible video header")
            header.extend(chunk)

        magic, size, expected_hash = struct.unpack(
            "<8sQ32s", header[:48]
        )

        if magic != MAGIC:
            raise ValueError("Not a Binary Waterfall reversible video")

        remaining = size
        digest = hashlib.sha256()

        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=".bw-recovery-",
            delete=False
        ) as output:
            temp_path = Path(output.name)

            while remaining:
                chunk = proc.stdout.read(min(CHUNK_SIZE, remaining))

                if not chunk:
                    raise ValueError("Video is missing original data")

                output.write(chunk)
                digest.update(chunk)
                remaining -= len(chunk)

        # Drain the remaining video padding.
        while proc.stdout.read(CHUNK_SIZE):
            pass

        returncode = proc.wait()
        reader.join()

        if returncode:
            raise RuntimeError(
                errors.decode(errors="replace")
                or "FFmpeg decoding failed"
            )

        if digest.digest() != expected_hash:
            raise ValueError("SHA-256 verification failed")

        os.replace(temp_path, destination)
        temp_path = None

        print(f"Recovered {size} bytes to {destination}")
        print("SHA-256 verified: exact recovery!")

    except Exception:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        reader.join()

        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

        raise

    finally:
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None and not stream.closed:
                stream.close()


def main():
    parser = argparse.ArgumentParser(
        description="Reversible Binary Waterfall video encoder/decoder"
    )

    parser.add_argument("action", choices=["encode", "decode"])
    parser.add_argument("source")
    parser.add_argument("destination")

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output file"
    )

    args = parser.parse_args()

    if args.action == "encode":
        encode(args.source, args.destination, overwrite=args.overwrite)
    else:
        decode(args.source, args.destination, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
