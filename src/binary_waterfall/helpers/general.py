import os


def make_file_path(filename):
    file_path, file_title = os.path.split(filename)
    os.makedirs(file_path, exist_ok=True)


def invert_bytes(bytestring):
    return bytes([0xFF - x for x in bytestring])
