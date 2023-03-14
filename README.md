# binary-waterfall
An audio-visual viewer for binary files.
 
[Inspired by this video.](https://www.youtube.com/watch?v=NFe0aGO9-TE)

[Click here to download the program for Windows!](https://github.com/nimaid/binary-waterfall/releases/latest)

If you use this for a video, please credit me as "nimaid", and provide a link to this GitHub.

Syntax help:
```
> python binary-waterfall.py -h
usage: binary-waterfall.py [-h] -f FILE [-vw VISWIDTH] [-vh VISHEIGHT] [-fs FPS]
                           [-ws WINDOWSIZE] [-cf COLORFORMAT] [-v VOLUME]
                           [-ac AUDIOCHANNELS] [-ab AUDIOBYTES] [-ar AUDIORATE] [-p]

Visualizes binary files with audio and video.

Default parameters are shown in [brackets].

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  the name of the file to visualize
  -vw VISWIDTH, --viswidth VISWIDTH
                        the width of the visualization [48]
  -vh VISHEIGHT, --visheight VISHEIGHT
                        the height of the visualization [48]
  -fs FPS, --fps FPS    the maximum framerate of the visualization [120]
  -ws WINDOWSIZE, --windowsize WINDOWSIZE
                        the length of the longest edge of the viewer window [600]
  -cf COLORFORMAT, --colorformat COLORFORMAT
                        how to interpret the bytes into colored pixels, requires exactly one
                        of each "r", "g", and "b" character, and can have any number of
                        unused bytes with an "x" character [rgbx]
  -v VOLUME, --volume VOLUME
                        the audio playback volume, from 0 to 100 [100]
  -ac AUDIOCHANNELS, --audiochannels AUDIOCHANNELS
                        how many channels to make in audio (1 is mono, 2 is stereo) [1]
  -ab AUDIOBYTES, --audiobytes AUDIOBYTES
                        how many bytes each sample uses (1 is 8-bit, 2 is 16-bit, etc.) [1]
  -ar AUDIORATE, --audiorate AUDIORATE
                        the sample rate to use [32000]
  -p, --pause           add to make the program pause before playing (useful for screen
                        recorder setup)
```

To get the results from [the inspiration video](https://www.youtube.com/watch?v=NFe0aGO9-TE):
```
python binary-waterfall.py examples\mspaint.exe
```

To get the results from [my SnippingTool.exe video](https://youtu.be/yZ38UzCo4QM):
```
python binary-waterfall.py -f examples\SnippingTool.exe -vw 96 -vh 96
```