# binary-waterfall
An audio-visual viewer for binary files.
 
[Inspired by this video.](https://www.youtube.com/watch?v=NFe0aGO9-TE)

If you use this for a video, please credit me as "nimaid", and provide a link to this GitHub.

Syntax help:
```
>python binary-waterfall.py -h
usage: binary-waterfall.py [-h] -f FILE [-vw VISWIDTH] [-vh VISHEIGHT] [-fs FPS] [-ws WINDOWSIZE] [-v VOLUME]
                           [-ac AUDIOCHANNELS] [-ab AUDIOBYTES] [-ar AUDIORATE] [-p]

Visualizes binary files with audio and video

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  the name of the file to visualize
  -vw VISWIDTH, --viswidth VISWIDTH
                        the width of the visualization
  -vh VISHEIGHT, --visheight VISHEIGHT
                        the width of the visualization
  -fs FPS, --fps FPS    the maximum framerate of the visualization
  -ws WINDOWSIZE, --windowsize WINDOWSIZE
                        the length of the longest edge of the viewer window
  -v VOLUME, --volume VOLUME
                        The audio playback volume, from 0 to 100
  -ac AUDIOCHANNELS, --audiochannels AUDIOCHANNELS
                        how many channels to make in audio (1 is mono, default)
  -ab AUDIOBYTES, --audiobytes AUDIOBYTES
                        how many bytes each sample uses (1 is 8-bit, 2 is 16-bit, etc.)
  -ar AUDIORATE, --audiorate AUDIORATE
                        the sample rate to use
  -p, --pause           if the program should pause before playing (useful for screen recorder setup)
```

To get the results from [the inspiration video](https://www.youtube.com/watch?v=NFe0aGO9-TE):
```
python binary-waterfall.py examples\mspaint.exe
```

To get the results from [my SnippingTool.exe video](https://youtu.be/yZ38UzCo4QM):
```
python binary-waterfall.py -f examples\SnippingTool.exe -vw 96 -vh 96
```