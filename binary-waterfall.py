import os

# https://www.youtube.com/watch?v=NFe0aGO9-TE
# https://www.youtube.com/watch?v=HFgqyB7hm3Y
# https://stackoverflow.com/questions/52369925/creating-wav-file-from-bytes
class BinaryWaterfall:
    def __init__(self, filename):
        self.name = filename
        
        with open(self.name, "rb") as f:
            self.bytes = f.read()
    
    def get_hex(self, caps=True):
        file_hex = self.bytes.hex()
        if caps:
            file_hex = file_hex.upper()
        return file_hex
    
    def save_hex(
        self,
        filename=None,
        caps=True
    ):
        if filename is None:
            filename = self.name + os.path.extsep + "txt"
        file_hex = self.get_hex(caps=caps)
        with open(filename, "w") as f:
            f.write(file_hex)
        return filename