from . import enums

DEFAULTS = {
    "width": 48,
    "height": 48,
    "color_format_string": "bgrx",
    "num_channels": 1,
    "sample_bytes": 1,
    "sample_rate": 32000,
    "volume": 100,
    "flip_v": True,
    "flip_h": False,
    "alignment": enums.AlignmentCode.MIDDLE,
    "player_fps": 120
}
