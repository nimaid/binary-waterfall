import os
import sys

from . import version
from .enums import PlatformCode

# Set platform dependent variables
USER_DIR = os.path.expanduser("~")

if sys.platform == PlatformCode.WINDOWS.value:
    PLATFORM = PlatformCode.WINDOWS
    APPDATA_DIR = os.path.join(USER_DIR, "AppData", "Roaming")
elif sys.platform == PlatformCode.LINUX.value:
    PLATFORM = PlatformCode.LINUX
    APPDATA_DIR = os.path.join(USER_DIR, ".local", "share")
elif sys.platform == PlatformCode.MAC.value:
    PLATFORM = PlatformCode.MAC
    APPDATA_DIR = os.path.join(USER_DIR, "Library", "Application Support")
else:
    PLATFORM = PlatformCode.UNKNOWN
    # Unknown platform, save to wherever os.path thinks the home dir is
    APPDATA_DIR = USER_DIR

DATA_DIR = os.path.join(APPDATA_DIR, version.TITLE)
