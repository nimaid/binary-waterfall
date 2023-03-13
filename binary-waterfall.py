import os
import wave

# https://www.youtube.com/watch?v=NFe0aGO9-TE
# https://www.youtube.com/watch?v=HFgqyB7hm3Y

class BinaryWaterfall:
    def __init__(self, filename):
        self.filename = filename
        
        with open(self.filename, "rb") as f:
            self.bytes = f.read()
        
        self.hex_filename = None
        self.wav_filename = None
    
    def get_hex(self, caps=True):
        file_hex = self.bytes.hex()
        if caps:
            file_hex = file_hex.upper()
        return file_hex
    
    def save_hex_file(
        self,
        filename=None,
        caps=True
    ):
        if filename is None:
            filename = self.filename + os.path.extsep + "txt"
        
        file_hex = self.get_hex(caps=caps)
        with open(filename, "w") as f:
            f.write(file_hex)
        
        self.hex_filename = filename
        return self.hex_filename
    
    def save_audio_file(
        self,
        filename=None,
        channels=1,
        sample_bytes=1,
        framerate=32000
    ):
        if filename is None:
            filename = self.filename + os.path.extsep + "wav"
        
        with wave.open(filename, "wb") as f:
            f.setnchannels(channels)
            f.setsampwidth(sample_bytes) # Number of bytes, 1 = 8-bit, 2 = 16-bit, etc.
            f.setframerate(framerate) # Also called sample rate
            f.writeframesraw(self.bytes)
        
        self.wav_filename = filename
        return self.wav_filename
        