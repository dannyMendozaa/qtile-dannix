#!/usr/bin/env python

# Daniel Mendoza
# Robotics Engineer

import dbus
from pathlib import Path
import time
import re
import subprocess as sp
import sys


videos = str(Path.home()) + '/Videos/'
script_path = str(Path(__file__).parent.absolute()) + '/'
sp.run(f'rm -f {script_path}*.mp4',shell=True,stdout=sp.DEVNULL)

bus = dbus.SessionBus()

s = None
for service in bus.list_names():
    if service.startswith('org.mpris.MediaPlayer2.'):
        try:
            ffox = re.findall(r'\bf[irefox]*\b',service)[0]
        except IndexError:
            continue
        if ffox:
            s = service
            break
if not s:
    sys.exit("[ERROR] firefox player not found")
ffox_player = dbus.SessionBus().get_object(s, '/org/mpris/MediaPlayer2')
meta = dbus.Interface(ffox_player, 
        dbus_interface='org.freedesktop.DBus.Properties')
metadata = meta.GetAll('org.mpris.MediaPlayer2.Player')
if metadata['PlaybackStatus'] == 'Playing':
    album = metadata['Metadata']['xesam:album']
    artist = str(metadata['Metadata']['xesam:artist'][0])
    album_cover = metadata['Metadata']['mpris:artUrl'].replace('file://','')
    song = metadata['Metadata']['xesam:title']
else:
    sys.exit("[ERROR] firefox player is paused")


# OUTPUT
def print_to_terminal():
    data = f"""

        {'Album':<7}: {album}
        {'Artist':<7}: {artist}
        {'Song':<7}: {song}

    """
    return data


# Get album cover - wget and imagemagick required
def cover(image):
    # Validate if the size of the album cover is 640x640
    # if the size is different it will be changed to 640x640
    image_size1 = sp.Popen(
            ['file', image], stdout=sp.PIPE)
    image_size2 = sp.Popen(
            ["awk {'print $5\"x\"$7'}"],
            shell=True, stdin=image_size1.stdout, stdout=sp.PIPE)
    image_size1.stdout.close()
    image_size3 = sp.Popen(
            ['tr', '-d', '\,'],
            text=True, stdin=image_size2.stdout, stdout=sp.PIPE, stderr=sp.PIPE)
    image_size2.stdout.close()
    size = image_size3.communicate()[0]
    if size != '540x540':
        convert = sp.Popen(
                ['convert', image, 
                    '-resize', '640x640!', image],
                stdout=sp.PIPE,
                stderr=sp.DEVNULL)
        convert.communicate()[0]
    return image

# Check if the track already exists
def mp4_exists(track):
    counter = 0
    track_exists = Path(track)
    while track_exists.is_file():
        counter += 1
        track = f'{videos}API_{artist}_{song}_{counter}.mp4'
        track_exists = Path(track)
    return track

# Record ("30" secs) audio from your computer 
def record(image):

    recorded = sp.Popen(
            ['ffmpeg','-y','-framerate','1','-i',image,
            '-f','pulse','-i','default','-t','30','-vf','format=yuv420p',
            f'{script_path}API_{artist}_{song}.mp4'
            ],stdout=sp.PIPE, stderr=sp.DEVNULL)

    return recorded.communicate()

def add_thumbnail(video,image):
    thumb = sp.Popen(
            ['ffmpeg','-y','-i',video,'-vf',"thumbnail,scale=320:320",
                '-frames:v','1',image,
            ],stdout=sp.PIPE, stderr=sp.DEVNULL)
    thumb.communicate()[0]

    thumbnailed = sp.Popen(
            ['ffmpeg','-y','-i',video,'-i',image,
                '-map','1','-map','0','-c','copy','-disposition:0','attached_pic',
                f'{track}'
            ],stdout=sp.PIPE, stderr=sp.DEVNULL)

    return thumbnailed.communicate()

print(print_to_terminal())
cover(album_cover)
track = f'{videos}API_{artist}_{song}.mp4'
track = mp4_exists(track)
record(album_cover)
add_thumbnail(f'{script_path}API_{artist}_{song}.mp4',f'{script_path}thumb.png')
