from .general import grouper


def invert_bytes(bytestring):
    return bytes([0xFF - x for x in bytestring])


def desaturate_rgb_byte(bytestring):
    r = bytestring[0]
    g = bytestring[1]
    b = bytestring[2]

    gray_value = round((min(r, g, b) + max(r, g, b)) / 2)

    desaturated = bytes([gray_value, gray_value, gray_value])

    return desaturated


def desaturate_rgb_bytes(bytestring):
    result = bytes()
    for byte in grouper(bytestring, 3, 0x00):
        result += desaturate_rgb_byte(byte)

    return result
