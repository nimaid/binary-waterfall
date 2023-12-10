import os
import re

from . import constants


class KeyValidate:
    def __init__(self, program_id):
        self.program_id = program_id.strip()
        self.program_int = 0
        for x in self.program_id:
            self.program_int += ord(x)
        self.program_int %= 0x10000
        self.program_offset = self.program_int % 5

    def get_program_hex(self):
        hex_string = hex(self.program_int)[2:].upper()
        while len(hex_string) < 4:
            hex_string = "0" + hex_string
        return hex_string

    def get_magic(self, hex_string=None):
        if hex_string is None:
            hex_string = self.get_program_hex()
        int_list = [int(x, 16) for x in hex_string]
        offset = int_list[0]
        magic_list = [(x - offset) % 16 for x in int_list]
        magic = "".join([hex(x)[2:] for x in magic_list]).upper()

        return magic

    def is_key_valid(self, key):
        if not re.match(r"^[A-F0-9]{5}-[A-F0-9]{5}-[A-F0-9]{5}-[A-F0-9]{5}$", key):
            return False

        groups = key.split("-")
        magic_hex = ""
        for idx, group in enumerate(groups):
            key_idx = (self.program_int - idx) % 5
            magic_hex += group[key_idx]

        if self.get_magic(magic_hex) == self.get_magic():
            return True
        else:
            return False


KEY_FILE = os.path.join(constants.DATA_DIR, "key")

if os.path.isfile(KEY_FILE):
    with open(KEY_FILE, "r") as f:
        SERIAL_KEY = f.read()
    SERIAL_KEY = SERIAL_KEY.strip("\n").strip("\r").strip()
    IS_REGISTERED = KeyValidate(constants.TITLE).is_key_valid(SERIAL_KEY)

    if not IS_REGISTERED:
        os.remove(KEY_FILE)
        SERIAL_KEY = None
else:
    IS_REGISTERED = False
    SERIAL_KEY = None
if not constants.IS_EXE:
    IS_REGISTERED = True
