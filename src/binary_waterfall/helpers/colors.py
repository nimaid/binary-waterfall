from .general import grouper


def get_luminance(r, g, b):
    return ((0.299 * r) + (0.587 * g) + (0.114 * b)) / 0xFF


def pick_shade_from_luminance(r, g, b, light_shade=0xFF, dark_shade=0x00):
    if get_luminance(r, g, b) < 0.5:
        return light_shade, light_shade, light_shade
    else:
        return dark_shade, dark_shade, dark_shade


def desaturate(r, g, b):
    gray_value = round((min(r, g, b) + max(r, g, b)) / 2)

    return gray_value, gray_value, gray_value


def invert(r, g, b):
    return (0xFF - x for x in [r, g, b])


def average(r1, g1, b1, r2, g2, b2):
    return (round((x + y) / 2) for x, y in zip((r1, g1, b1), (r2, g2, b2)))


def split_rgb_byte(bytestring):
    r = bytestring[0]
    g = bytestring[1]
    b = bytestring[2]

    return r, g, b


def filter_rgb_bytes(bytestring, filter_function):
    result = bytes()
    for byte in grouper(bytestring, 3, 0x00):
        r, g, b = split_rgb_byte(byte)
        r_filtered, g_filtered, b_filtered = filter_function(r, g, b)
        result += bytes([r_filtered, g_filtered, b_filtered])

    return result


def average_rgb_bytes(bytestring_a, bytestring_b):
    result = bytes()
    for byte_a, byte_b in zip(grouper(bytestring_a, 3, 0x00), grouper(bytestring_b, 3, 0x00)):
        r_a, g_a, b_a = split_rgb_byte(byte_a)
        r_b, g_b, b_b = split_rgb_byte(byte_b)
        r_average, g_average, b_average = average(r_a, g_a, b_a, r_b, g_b, b_b)
        result += bytes([r_average, g_average, b_average])

    return result
