import os
import wave
import contextlib
with contextlib.redirect_stdout(None):
    import pygame

# https://www.youtube.com/watch?v=NFe0aGO9-TE
# https://www.youtube.com/watch?v=HFgqyB7hm3Y

class BinaryWaterfall:
    def __init__(self, filename, width=48, height=48):
        self.filename = filename
        
        self.width = width
        self.height = height
        self.used_color_bytes = 3
        self.dead_color_bytes = 1
        self.color_bytes = self.used_color_bytes + self.dead_color_bytes
        
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
    
    def get_image(
        self,
        address
    ):
        picture_bytes = bytes()
        current_address = address
        for row in range(self.height):
            for col in range(self.width):
                picture_bytes += self.bytes[current_address:current_address+1] # Red
                current_address += 1
                picture_bytes += self.bytes[current_address:current_address+1] # Green
                current_address += 1
                picture_bytes += self.bytes[current_address:current_address+1] # Blue
                current_address += 1
                
                current_address += self.dead_color_bytes # Skip bytes for visual
        
        full_length = (self.width * self.height * self.used_color_bytes)
        picture_bytes_length = len(picture_bytes)
        # Pad picture data
        if picture_bytes_length < full_length:
            pad_length = full_length - picture_bytes_length
            picture_bytes += b"\x00" * pad_length
        # Tell that we are past the end of the file
        if picture_bytes_length == 0:
            current_address = -1
        picture = pygame.image.frombytes(picture_bytes, (self.width, self.height), 'RGB', True)
        return picture, current_address



pygame.init()
X = 600
Y = 600

screen = pygame.display.set_mode((X, Y))
pygame.display.set_caption('image')

waterfall = BinaryWaterfall(os.path.sep.join(["examples", "mspaint.exe"]))
waterfall.save_audio_file() # Create wave file

run_program = True
address = 0
while run_program:
    for i in pygame.event.get():
        if i.type == pygame.QUIT:
            run_program = False
    
    image, end_address = waterfall.get_image(address)
    image = pygame.transform.scale(image, (X, Y))
    screen.blit(image, (0, 0))
    pygame.display.flip()
    
    address += waterfall.width * waterfall.color_bytes
    
    if end_address == -1:
        run_program = False
    
    pygame.time.wait(10)
pygame.quit()
