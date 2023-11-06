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
        color_format="bgrx",
        num_channels=1,
        sample_bytes=1,
        sample_rate=32000,
        start_paused=False,
        longest_side=600,
        volume=100,
        fps=120,
        save_audio=False
    ):
        self.filename = filename
        
        self.width = width
        self.height = height
        self.dim = (self.width, self.height)
        
        self.num_channels = num_channels
        self.sample_bytes = sample_bytes
        self.sample_rate = sample_rate
        
        self.start_paused = start_paused
        self.save_audio = save_audio
        
        self.audio_path = PROG_PATH # Save the wav file to the program path (NOT the binary file's path!)
        
        self.volume = volume
        
        self.longest_side = longest_side
        
        self.fps = fps
        
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
        
        if self.num_channels not in [1, 2]:
            raise argparse.ArgumentError("Invalid number of audio channels, must be either 1 or 2")
        
        if self.sample_bytes not in [1, 2, 3, 4]:
            raise argparse.ArgumentError("Invalid sample size (bytes), must be either 1, 2, 3, or 4")
        
        if self.sample_rate < 1:
            raise argparse.ArgumentError("Invalid sample rate, must be at least 1")
        
        if self.width < 4:
            raise argparse.ArgumentError("Visualization width must be at least 4")
        
        if self.height < 4:
            raise argparse.ArgumentError("Visualization height must be at least 4")
        
        if self.volume < 0 or self.volume > 100:
            raise argparse.ArgumentError("Volume must be between 0 and 100")
        
        # Determine if the window must be scaled, and check for errors
        min_window_size = 600  # Default for args.long_edge_length
        if self.width > self.height:
            largest_view_dim = self.width
        else:
            largest_view_dim = self.height
            
        self.scale = True
        if self.longest_side == -1:
            if min_window_size > largest_view_dim:
                window_size = min_window_size
            else:
                window_size = largest_view_dim
                self.scale = False
        else:
            window_size = self.longest_side
            if window_size <= largest_view_dim:
                self.scale = False
        
        # Determine actual window size
        if self.width > self.height:
            self.window_width = window_size
            self.window_height = round(self.height * window_size / self.width)
        else:
            self.window_height = window_size
            self.window_width = round(self.width * window_size / self.height)
        
        self.window_dim = (self.window_width, self.window_height)
        
        if window_size < self.height or window_size < self.width:
                raise argparse.ArgumentError("Window size is smaller than one of the visualization dimensions")
        
        if self.fps < 1:
            raise argparse.ArgumentError("FPS must be at least 1")
        
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
        path=None # Will save to the binary file's location if not set
    ):
        if filename is None:
            filename = self.filename + os.path.extsep + "wav"
        
        if path is not None:
            save_path, name = os.path.split(filename)
            save_path = path
            filename = os.path.join(save_path, name)
        
        with wave.open(filename, "wb") as f:
            f.setnchannels(self.num_channels)
            f.setsampwidth(self.sample_bytes)
            f.setframerate(self.sample_rate)
            f.writeframesraw(self.bytes)
        
        self.wav_channels = self.num_channels
        self.wav_sample_bytes = self.sample_bytes
        self.wav_samplerate = self.sample_rate
        
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
    
    def init_window(self):
        # Start pygame
        pygame.init()
        
        self.screen = pygame.display.set_mode(self.window_dim)
        binary_filename = os.path.split(self.filename)[-1]
        pygame.display.set_caption("Binary Waterfall - \"{}\"".format(binary_filename))
        pygame_icon = pygame.image.load(os.path.join(PATH, "icon.png"))
        pygame.display.set_icon(pygame_icon)
        self.fps_clock = pygame.time.Clock()
    
    def compute_audio(self):
        print("\nComputing audio...")
        try:
            self.file_audio = self.save_audio_file(path=self.audio_path) # Create wave file
            # Get file length in ms
            self.file_sound = pygame.mixer.Sound(self.file_audio)
            self.file_length_ms = math.ceil(self.file_sound.get_length() * 1000)
            del(self.file_sound)
        except KeyboardInterrupt:
            print("Audio computation interrupted, exiting...\n")
            pygame.quit()
            os.remove(file_audio)
            sys.exit()
    
    def init_sound(self):
        if self.start_paused:
            print("Ready to display file! [Press SPACE to play/pause]")
        else:
            print("Displaying file... [Press SPACE to pause/play]")
        
        # Start playing sound
        pygame.mixer.init()
        pygame.mixer.music.load(self.file_audio)
        pygame.mixer.music.set_volume(self.volume / 100)
        if self.start_paused:
            self.still_waiting = True
        else:
            pygame.mixer.music.play()
            self.still_waiting = False
        self.playing_audio = True
    
    def get_address(self, ms):
        address_block_size = self.width * self.color_bytes
        total_blocks = math.ceil(len(self.bytes) / address_block_size)
        address_block_offset = round(ms * total_blocks / self.file_length_ms)
        return address_block_offset * address_block_size
        
    
    def display_loop(self):
        # Run display loop
        run_program = True
        self.address = 0
        while run_program:
            try:
                # Events handler
                for event in pygame.event.get():
                    # Quit on exit
                    if event.type == pygame.QUIT:
                        run_program = False
                    
                    # Keypress handler
                    if event.type == pygame.KEYDOWN:
                        # Space plays and pauses
                        if event.key == pygame.K_SPACE:
                            if self.start_paused and self.still_waiting:
                                pygame.mixer.music.play()
                                self.still_waiting = False
                            elif self.playing_audio:
                                pygame.mixer.music.pause()
                                self.playing_audio = False
                            else:
                                pygame.mixer.music.unpause()
                                self.playing_audio = True
            
                if not self.still_waiting:
                    audio_ms = pygame.mixer.music.get_pos()
                    # If music is over
                    if audio_ms == -1:
                        run_program = False
                        break
                    
                    self.address = self.get_address(audio_ms)
                    
                    image, end_address = self.get_image(self.address)
                    if end_address == -1:
                        run_program = False
                    
                    if self.scale:
                        image = pygame.transform.scale(image, self.window_dim)
                    
                    self.screen.blit(image, (0, 0))
                    pygame.display.flip()
                    
                    self.fps_clock.tick(self.fps)
            except KeyboardInterrupt:
                run_program = False
                break
            
        pygame.quit()
    
    def run(self):
        self.init_window()
        self.compute_audio()
        self.init_sound()
        self.display_loop()

        # Delete audio file
        if self.save_audio:
            print("Audio file saved: \"{}\"".format(self.file_audio))
        else:
            print("Deleting audio file...")
            os.remove(self.file_audio)

        print("All done!\n")


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

    # Initialize main object
    waterfall = BinaryWaterfall(
        filename=args.filename,
        width=args.px_wide,
        height=args.px_tall,
        color_format=args.format_string,
        num_channels=args.channel_count,
        sample_bytes=args.bytes_per_sample,
        sample_rate=args.sample_rate,
        start_paused=args.do_pause,
        volume=args.volume_percentage,
        longest_side=args.long_edge_length,
        fps=args.fps,
        save_audio=args.do_save
    )
    
    # Run
    waterfall.run()

def run():
    main(sys.argv[1:])

if __name__ == "__main__":
    run()
