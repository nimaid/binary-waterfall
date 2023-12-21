import os
from itertools import zip_longest


def make_file_path(filename):
    file_path, file_title = os.path.split(filename)
    os.makedirs(file_path, exist_ok=True)


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)
