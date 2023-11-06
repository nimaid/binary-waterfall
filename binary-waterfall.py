import os
import sys
import math
import wave
import argparse
from enum import Enum
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

# Test if this is a PyInstaller executable or a .py file
if getattr(sys, 'frozen', False):
    IS_EXE = True
    PROG_FILE = sys.executable
    PROG_PATH = os.path.dirname(PROG_FILE)
    PATH = sys._MEIPASS
else:
    IS_EXE = False
    PROG_FILE = os.path.realpath(__file__)
    PROG_PATH = os.path.dirname(PROG_FILE)
    PATH = PROG_PATH

# Main class
class BinaryWaterfall:
    def __init__(
        self, filename,
        width=48,
        height=48,
        color_format="bgrx"
    ):
        self.filename = filename
        
        self.width = width
        self.height = height
        
        color_format = color_format.strip().lower()
        red_count = color_format.count(self.ColorFmtCode.RED.value)
        if red_count != 1:
            raise ValueError(
            "Exactly 1 red channel format specifier \"{}\" needed, but {} were given in format string \"{}\"".format(
                self.ColorFmtCode.RED.value,
                red_count,
                color_format
            )
        )
        green_count = color_format.count(self.ColorFmtCode.GREEN.value)
        if green_count != 1:
            raise ValueError(
            "Exactly 1 green channel format specifier \"{}\" needed, but {} were given in format string \"{}\"".format(
                self.ColorFmtCode.GREEN.value,
                green_count,
                color_format
            )
        )
        blue_count = color_format.count(self.ColorFmtCode.BLUE.value)
        if blue_count != 1:
            raise ValueError(
            "Exactly 1 blue channel format specifier \"{}\" needed, but {} were given in format string \"{}\"".format(
                self.ColorFmtCode.BLUE.value,
                blue_count,
                color_format
            )
        )
        unused_count = color_format.count(self.ColorFmtCode.UNUSED.value)
        
        read_color_byte_order = list()
        for c in color_format:
            if c not in self.ColorFmtCode.VALID_OPTIONS.value:
                raise ValueError(
                    "Color formatting codes only accept \"{}\" = red, \"{}\" = green, \"{}\" = blue, \"{}\" = unused".format(
                        self.ColorFmtCode.RED.value.
                        self.ColorFmtCode.GREEN.value,
                        self.ColorFmtCode.BLUE.value,
                        self.ColorFmtCode.UNUSED.value
                    )
                )
            
            if c == self.ColorFmtCode.RED.value:
                read_color_byte_order.append(self.ColorFmtCode.RED)
            elif c == self.ColorFmtCode.GREEN.value:
                read_color_byte_order.append(self.ColorFmtCode.GREEN)
            elif c == self.ColorFmtCode.BLUE.value:
                read_color_byte_order.append(self.ColorFmtCode.BLUE)
            elif c == self.ColorFmtCode.UNUSED.value:
                read_color_byte_order.append(self.ColorFmtCode.UNUSED)
        
        self.used_color_bytes = red_count + green_count + blue_count
        self.dead_color_bytes = unused_count
        self.color_bytes = self.used_color_bytes + self.dead_color_bytes
        self.color_format = read_color_byte_order
        
        with open(self.filename, "rb") as f:
            self.bytes = f.read()
        
        self.wav_filename = None
        self.wav_channels = None
        self.wav_sample_bytes = None
        self.wav_sample_rate = None
    
    class ColorFmtCode(Enum):
        RED = "r"
        GREEN = "g"
        BLUE = "b"
        UNUSED = "x"
        VALID_OPTIONS = "rgbx"
    
    def save_audio_file(
        self,
        filename=None, # Will set itself based on the input filename if left set to None
        path=None, # Will save to the binary file's location if not set
        channels=1, # Number of channels, 1 = Mono, 2 = Stereo, etc.
        sample_bytes=1, # Number of bytes per sample, 1 = 8-bit, 2 = 16-bit, etc.
        sample_rate=32000 # The sample rate of the file
    ):
        if filename is None:
            filename = self.filename + os.path.extsep + "wav"
        
        if path is not None:
            save_path, name = os.path.split(filename)
            save_path = path
            filename = os.path.join(save_path, name)
        
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
                # Fill one RGB byte value
                this_byte = [b'\x00', b'\x00', b'\x00']
                for c in self.color_format:
                    if c == self.ColorFmtCode.RED:
                        this_byte[0] = self.bytes[current_address:current_address+1] # Red
                    elif c == self.ColorFmtCode.GREEN:
                        this_byte[1] = self.bytes[current_address:current_address+1] # Green
                    elif c == self.ColorFmtCode.BLUE:
                        this_byte[2] = self.bytes[current_address:current_address+1] # Blue
                    current_address += 1
                    
                picture_bytes += b"".join(this_byte)
        
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



# Helper functions for the argument parser
def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)

# Parse arguments
def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Visualizes binary files with audio and video.\n\nDefault parameters are shown in [brackets].",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-f", "--file", dest="filename", type=file_path, required=True,
        help="the name of the file to visualize")
    parser.add_argument("-vw", "--viswidth", dest="px_wide", type=int, required=False, default=48,
        help="the width of the visualization [48]")
    parser.add_argument("-vh", "--visheight", dest="px_tall", type=int, required=False, default=48,
        help="the height of the visualization [48]")
    parser.add_argument("-fs", "--fps", dest="fps", type=int, required=False, default=120,
        help="the maximum framerate of the visualization [120]")
    parser.add_argument("-ws", "--windowsize", dest="long_edge_length", type=int, required=False, default=-1,
        help="the length of the longest edge of the viewer window [600]")
    parser.add_argument("-cf", "--colorformat", dest="format_string", type=str, required=False, default="bgrx",
        help="how to interpret the bytes into colored pixels, requires exactly one of each \"r\", \"g\", and \"b\" character, and can have any number of unused bytes with an \"x\" character [bgrx]")
    parser.add_argument("-v", "--volume", dest="volume_percentage", type=int, required=False, default=100,
        help="the audio playback volume, from 0 to 100 [100]")
    parser.add_argument("-ac", "--audiochannels", dest="channel_count", type=int, required=False, default=1,
        help="how many channels to make in audio (1 is mono, 2 is stereo) [1]")
    parser.add_argument("-ab", "--audiobytes", dest="bytes_per_sample", type=int, required=False, default=1,
        help="how many bytes each sample uses (1 is 8-bit, 2 is 16-bit, etc.) [1]")
    parser.add_argument("-ar", "--audiorate", dest="sample_rate", type=int, required=False, default=32000,
        help="the sample rate to use [32000]")
    parser.add_argument("-sa", "--saveaudio", dest="do_save", action="store_true",
        help="add to prevent the program from deleting the computed .wav file")
    parser.add_argument("-p", "--pause", dest="do_pause", action="store_true",
        help="add to make the program pause before playing (useful for screen recorder setup)")
    
    return parser.parse_args()

def main(args):
    args = parse_args(args)
    
    # Validate arguments and set local vars
    min_window_size = 600
    
    waterfall_file = args.filename

    if args.px_wide < 4:
        raise argparse.ArgumentError("Visualization width must be at least 4")
    view_width = args.px_wide
    if args.px_tall < 4:
        raise argparse.ArgumentError("Visualization height must be at least 4")
    view_height = args.px_tall

    if view_width > view_height:
        largest_view_dim = view_width
    else:
        largest_view_dim = view_height

    scale_window = True
    if args.long_edge_length == -1:
        if min_window_size > largest_view_dim:
            window_size = min_window_size
        else:
            window_size = largest_view_dim
            scale_window = False
    else:
        window_size = args.long_edge_length
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

    if args.fps < 1:
            raise argparse.ArgumentError("FPS must be at least 1")
    fps = args.fps

    if args.channel_count not in [1, 2]:
            raise argparse.ArgumentError("Invalid number of audio channels, must be either 1 or 2")
    audio_channels = args.channel_count

    if args.bytes_per_sample not in [1, 2, 3, 4]:
            raise argparse.ArgumentError("Invalid sample size (bytes), must be either 1, 2, 3, or 4")
    audio_sample_bytes = args.bytes_per_sample

    if args.sample_rate < 1:
            raise argparse.ArgumentError("Invalid sample rate, must be at least 1")
    audio_sample_rate = args.sample_rate

    wait_for_play = args.do_pause

    audio_volume = args.volume_percentage
    if audio_volume < 0 or audio_volume > 100:
        raise argparse.ArgumentError("Volume must be between 0 and 100")

    audio_volume_val = audio_volume / 100 

    color_format = args.format_string

    save_audio = args.do_save

    audio_path = PROG_PATH # Save the wav file to the program path (NOT the binary file's path!)
    
    # Start pygame
    pygame.init()

    waterfall = BinaryWaterfall(
        waterfall_file,
        width=view_width,
        height=view_height,
        color_format=color_format
    )

    print("\nComputing audio...")
    try:
        file_audio = waterfall.save_audio_file(
            channels=audio_channels,
            sample_bytes=audio_sample_bytes,
            sample_rate=audio_sample_rate,
            path=audio_path
        ) # Create wave file
        # Get file length in ms
        file_sound = pygame.mixer.Sound(file_audio)
        file_length_ms = math.ceil(file_sound.get_length() * 1000)
        del(file_sound)
    except KeyboardInterrupt:
        print("Audio computation interrupted, exiting...\n")
        pygame.quit()
        os.remove(file_audio)
        sys.exit()

    screen = pygame.display.set_mode((window_width, window_height))
    binary_filename = os.path.split(waterfall.filename)[-1]
    pygame.display.set_caption("Binary Waterfall - \"{}\"".format(binary_filename))
    pygame_icon = pygame.image.load(os.path.join(PATH, "icon.png"))
    pygame.display.set_icon(pygame_icon)
    fps_clock = pygame.time.Clock()

    if wait_for_play:
        print("Ready to display file! [Press SPACE to play/pause]")
    else:
        print("Displaying file... [Press SPACE to pause/play]")
    # Start playing sound
    pygame.mixer.init()
    pygame.mixer.music.load(file_audio)
    pygame.mixer.music.set_volume(audio_volume_val)
    if wait_for_play:
        still_waiting = True
    else:
        pygame.mixer.music.play()
        still_waiting = False
    playing_audio = True
    # Run display loop
    run_program = True
    address = 0
    address_block_size = waterfall.width * waterfall.color_bytes
    total_blocks = math.ceil(len(waterfall.bytes) / address_block_size)
    while run_program:
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run_program = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if wait_for_play and still_waiting:
                            pygame.mixer.music.play()
                            still_waiting = False
                        elif playing_audio:
                            pygame.mixer.music.pause()
                            playing_audio = False
                        else:
                            pygame.mixer.music.unpause()
                            playing_audio = True
        
            if not still_waiting:
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
        except KeyboardInterrupt:
            run_program = False
            break
        
    pygame.quit()

    # Delete audio file
    if save_audio:
        print("Audio file saved: \"{}\"".format(file_audio))
    else:
        print("Deleting audio file...")
        os.remove(file_audio)

    print("All done!\n")

def run():
    main(sys.argv[1:])

if __name__ == "__main__":
    run()
