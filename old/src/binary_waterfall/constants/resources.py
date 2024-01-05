import os

from . import paths

RESOURCE_PATH = os.path.join(paths.PATH, "resources")

# A dict to store icon locations
ICON_PATHS = {
    "program": os.path.join(RESOURCE_PATH, "icon.png"),
    "button": {
        "play": {
            "base": os.path.join(RESOURCE_PATH, "play.png"),
            "clicked": os.path.join(RESOURCE_PATH, "playC.png"),
            "hover": os.path.join(RESOURCE_PATH, "playH.png")
        },
        "pause": {
            "base": os.path.join(RESOURCE_PATH, "pause.png"),
            "clicked": os.path.join(RESOURCE_PATH, "pauseC.png"),
            "hover": os.path.join(RESOURCE_PATH, "pauseH.png")
        },
        "back": {
            "base": os.path.join(RESOURCE_PATH, "back.png"),
            "clicked": os.path.join(RESOURCE_PATH, "backC.png"),
            "hover": os.path.join(RESOURCE_PATH, "backH.png")
        },
        "forward": {
            "base": os.path.join(RESOURCE_PATH, "forward.png"),
            "clicked": os.path.join(RESOURCE_PATH, "forwardC.png"),
            "hover": os.path.join(RESOURCE_PATH, "forwardH.png")
        },
        "restart": {
            "base": os.path.join(RESOURCE_PATH, "restart.png"),
            "clicked": os.path.join(RESOURCE_PATH, "restartC.png"),
            "hover": os.path.join(RESOURCE_PATH, "restartH.png")
        }
    },
    "volume": {
        "base": os.path.join(RESOURCE_PATH, "volume.png"),
        "mute": os.path.join(RESOURCE_PATH, "mute.png")
    },
    "watermark": os.path.join(RESOURCE_PATH, "watermark.png")
}
