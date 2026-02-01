import pyffmpeg as ffmpeg

stream = ffmpeg.input('video.mp4').vflip().output('flipped.mp4')

# Get the command arguments
args = stream.compile()
print(args)