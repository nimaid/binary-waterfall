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
