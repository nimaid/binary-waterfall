import os


def make_file_path(filename):
    file_path, file_title = os.path.split(filename)
    os.makedirs(file_path, exist_ok=True)
