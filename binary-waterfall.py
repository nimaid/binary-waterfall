import os
import math
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

waterfall = BinaryWaterfall(os.path.sep.join(["examples", "mspaint.exe"]))

screen = pygame.display.set_mode((X, Y))
pygame.display.set_caption(os.path.split(waterfall.filename)[-1])
fps_clock = pygame.time.Clock()
fps = 60

print("Computing audio...")
file_audio = waterfall.save_audio_file() # Create wave file
file_length_ms = math.ceil(pygame.mixer.Sound(file_audio).get_length() * 1000)


print("Displaying file...")
# Start playing sound
pygame.mixer.init()
pygame.mixer.music.load(file_audio)
pygame.mixer.music.play()
# Run display loop
run_program = True
address = 0
address_block_size = waterfall.width * waterfall.color_bytes
total_blocks = math.ceil(len(waterfall.bytes) / address_block_size)
while run_program:
    for i in pygame.event.get():
        if i.type == pygame.QUIT:
            run_program = False
    
    audio_ms = pygame.mixer.music.get_pos()
    # If music is over
    if audio_ms == -1:
        run_program = False
        break
    
    address_block_offset = round(audio_ms * total_blocks / file_length_ms)
    address = address_block_offset * address_block_size
    
    image, end_address = waterfall.get_image(address)
    if end_address == -1:
        run_program = False

    image = pygame.transform.scale(image, (X, Y))
    screen.blit(image, (0, 0))
    pygame.display.flip()
    
    fps_clock.tick(fps)
    
pygame.quit()

print("All done!")