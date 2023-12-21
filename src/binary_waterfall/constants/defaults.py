from . import enums

DEFAULTS = {
    "width": 48,
    "height": 48,
    "color_format_string": "bgrx",
    "num_channels": 1,
    "sample_bytes": 1,
    "sample_rate": 32000,
    "file_volume": 100,
    "flip_v": True,
    "flip_h": False,
    "alignment": enums.AlignmentCode.MIDDLE,
    "playhead_visible": True,
    "max_dim": 512,
    "player_fps": 120
}
