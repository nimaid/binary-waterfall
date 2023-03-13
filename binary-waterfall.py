import os
import wave
from PIL import Image
import pygame

# https://www.youtube.com/watch?v=NFe0aGO9-TE
# https://www.youtube.com/watch?v=HFgqyB7hm3Y

class BinaryWaterfall:
    def __init__(self, filename):
        self.filename = filename
        
        with open(self.filename, "rb") as f:
            self.bytes = f.read()
        
        self.wav_filename = None
        self.wav_channels = None
        self.wav_sample_bytes = None
        self.wav_sample_rate = None
    
    def get_hex(self, caps=True):
        file_hex = self.bytes.hex()
        if caps:
            file_hex = file_hex.upper()
        return file_hex
    
    def save_audio_file(
        self,
        filename=None, # Will set itself based on the input filename if left set to None
        channels=1, # Number of channels, 1 = Mono, 2 = Stereo, etc.
        sample_bytes=1, # Number of bytes per sample, 1 = 8-bit, 2 = 16-bit, etc.
        sample_rate=32000 # The sample rate of the file
    ):
        if filename is None:
            filename = self.filename + os.path.extsep + "wav"
        
        with wave.open(filename, "wb") as f:
            f.setnchannels(channels)
            f.setsampwidth(sample_bytes)
            f.setframerate(sample_rate)
            f.writeframesraw(self.bytes)
        
        self.wav_channels = channels
        self.wav_sample_bytes = sample_bytes
        self.wav_samplerate = sample_rate
        
        self.wav_filename = filename
        return self.wav_filename
    
    def process_files(self):
        hexfile = self.save_hex_file()
        print("Saved HEX file at: {}".format(hexfile))
        wavfile = self.save_audio_file()
        print("Saved WAV file at: {}".format(wavfile))
        return (hexfile, wavfile)
    