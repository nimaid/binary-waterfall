from enum import Enum


class PlatformCode(Enum):
    WINDOWS = "win32"
    LINUX = "linux"
    MAC = "darwin"
    UNKNOWN = "unknown"


class ColorFmtCode(Enum):
    RED = "r"
    GREEN = "g"
    BLUE = "b"
    WHITE = "w"
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
    MKV = ".mkv"
    AVI = ".avi"
