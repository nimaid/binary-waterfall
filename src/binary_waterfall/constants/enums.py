from enum import Enum


class PlatformCode(Enum):
    WINDOWS = "win32"
    LINUX = "linux"
    MAC = "darwin"
    UNKNOWN = "unknown"


class ColorFmtCode(Enum):
    RED = "r"
    RED_INV = "R"
    GREEN = "g"
    GREEN_INV = "G"
    BLUE = "b"
    BLUE_INV = "B"
    WHITE = "w"
    WHITE_INV = "W"
    UNUSED = "x"


class ColorModeCode(Enum):
    GRAYSCALE = 0
    RGB = 1


class ImageFormatCode(Enum):
    JPEG = ".jpg"
    PNG = ".png"
    BITMAP = ".bmp"


class AudioFormatCode(Enum):
    WAVE = ".wav"
    MP3 = ".mp3"
    FLAC = ".flac"


class VideoFormatCode(Enum):
    MP4 = ".mp4"
    AVI = ".avi"


class VideoCodecCode(Enum):
    LIBX264 = "libx264"
    MPEG4 = "mpeg4"
    RAW = "rawvideo"
    PNG = "png"


class AudioCodecCode(Enum):
    MP3 = "libmp3lame"
    M4A = "libfdk_aac"
    WAV16 = "pcm_s16le"
    WAV32 = "pcm_s32le"


class EncoderPresetCode(Enum):
    ULTRAFAST = "ultrafast"
    SUPERFAST = "superfast"
    VERYFAST = "veryfast"
    FASTER = "faster"
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    SLOWER = "slower"
    VERYSLOW = "veryslow"
    PLACEBO = "placebo"


class AlignmentCode(Enum):
    START = 0
    END = 1
    MIDDLE = 2
