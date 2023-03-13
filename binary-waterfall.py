import os
import math
import wave
import argparse
import contextlib
with contextlib.redirect_stdout(None):
    import pygame


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



# Parse arguments
def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)
parser = argparse.ArgumentParser(description="Visualizes binary files with audio and video")
parser.add_argument("-f", "--file", type=file_path, required=True,
    help="the name of the file to visualize")
parser.add_argument("-vw", "--viswidth", type=int, required=False, default=48,
    help="the width of the visualization")
parser.add_argument("-vh", "--visheight", type=int, required=False, default=48,
    help="the width of the visualization")
parser.add_argument("-fs", "--fps", type=int, required=False, default=60,
    help="the maximum framerate of the visualization")
parser.add_argument("-ws", "--windowsize", type=int, required=False, default=-1,
    help="the length of the longest edge of the viewer window")
parser.add_argument("-ac", "--audiochannels", type=int, required=False, default=1,
    help="how many channels to make in audio (1 is mono, default)")
parser.add_argument("-ab", "--audiobytes", type=int, required=False, default=1,
    help="how many bytes each sample uses (1 is 8-bit, 2 is 16-bit, etc.)")
parser.add_argument("-ar", "--audiorate", type=int, required=False, default=32000,
    help="the sample rate to use")
args = vars(parser.parse_args())

waterfall_file = args["file"]

if args["viswidth"] < 4:
    raise argparse.ArgumentError("Visualization width must be at least 4")
view_width = args["viswidth"]
if args["visheight"] < 4:
    raise argparse.ArgumentError("Visualization height must be at least 4")
view_height = args["visheight"]

if view_width > view_height:
    largest_view_dim = view_width
else:
    largest_view_dim = view_height

min_window_size = 600
scale_window = True
if args["windowsize"] == -1:
    if min_window_size > largest_view_dim:
        window_size = min_window_size
    else:
        window_size = largest_view_dim
        scale_window = False
else:
    window_size = args["windowsize"]
    if window_size <= largest_view_dim:
        scale_window = False

if window_size < view_height or window_size < view_width:
        raise argparse.ArgumentError("Window size is smaller than one of the visualization dimensions")
   
if view_width > view_height:
    window_width = window_size
    window_height = round(view_height * window_size / view_width)
else:
    window_height = window_size
    window_width = round(view_width * window_size / view_height)

if args["fps"] < 1:
        raise argparse.ArgumentError("FPS must be at least 1")
fps = args["fps"]

if args["audiochannels"] not in [1, 2]:
        raise argparse.ArgumentError("Invalid number of audio channels, must be either 1 or 2")
audio_channels = args["audiochannels"]

if args["audiobytes"] not in [1, 2, 3, 4]:
        raise argparse.ArgumentError("Invalid sample size (bytes), must be either 1, 2, 3, or 4")
audio_sample_bytes = args["audiobytes"]

if args["audiorate"] < 1:
        raise argparse.ArgumentError("Invalid sample rate, must be at least 1")
audio_sample_rate = args["audiorate"]



# Start pygame
pygame.init()

waterfall = BinaryWaterfall(waterfall_file, width=view_width, height=view_height)

screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption(os.path.split(waterfall.filename)[-1])
fps_clock = pygame.time.Clock()

print("Computing audio...")
file_audio = waterfall.save_audio_file(
    channels=audio_channels,
    sample_bytes=audio_sample_bytes,
    sample_rate=audio_sample_rate
) # Create wave file
file_sound = pygame.mixer.Sound(file_audio)
file_length_ms = math.ceil(file_sound.get_length() * 1000)
del(file_sound)


print("Ready to play file! Get your camera ready!")
temp = input("Press Enter once you are ready to display the file!")


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
    
    if scale_window:
        image = pygame.transform.scale(image, (window_width, window_height))
    
    screen.blit(image, (0, 0))
    pygame.display.flip()
    
    fps_clock.tick(fps)
    
pygame.quit()

# Delete audio file
os.remove(file_audio)

print("All done!")