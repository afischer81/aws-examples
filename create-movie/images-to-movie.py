#!/usr/bin/python3
#
#        file: images-to-movie.py
#
# description: create MP4 movie from a directory of image files
#
#      author: Alexander Fischer, 2021-02-18
#

import logging
import os
import shutil
import subprocess
import sys

self = os.path.basename(sys.argv[0])
myName = os.path.splitext(self)[0]
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(myName)
log.setLevel(logging.INFO)

ffmpegExe = '/usr/local/bin/ffmpeg'

inputDir = os.path.abspath(sys.argv[1])
videoFileName = os.path.abspath(sys.argv[2])

tmpDir = '/tmp'
if not os.path.exists(tmpDir):
    os.makedirs(tmpDir)

def AddText(inputFileName, text, pos, outputFileName):
    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw
    img = Image.open(inputFileName)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("DejaVuSans-Bold", 48)
    draw.text(pos, text, (255,255,0), font=font)
    img.save(outputFileName)

i = 1
for f in sorted(os.listdir(inputDir)):
    if not f.lower().endswith('.jpg'):
        log.warning('skipping ' + f)
        continue
    src = os.path.join(inputDir, f)
    timeStamp = os.path.splitext(f)[0].replace('_', ' ')
    timeStamp = timeStamp[11:13] + ':' + timeStamp[13:15]
    ext = os.path.splitext(f)[-1]
    dest = os.path.join(tmpDir, 'img_{:04d}'.format(i) + ext)
    log.info(src + '->' + dest)
    x = 2592 / 2 - 64
    y = 1944 - 56
    AddText(src, timeStamp, (x, y), dest)
    os.remove(src)
    i += 1

cmd = [ ffmpegExe, '-framerate', '5', '-i', os.path.join(tmpDir, 'img_%04d.jpg'), '-vf', 'scale=-1:1080', '-c:v', 'libx264', '-r', '25', '-pix_fmt', 'yuv420p', videoFileName
]
subprocess.call(cmd)
