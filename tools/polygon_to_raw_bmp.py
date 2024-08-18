"""
This tool converts the MicroHydra 1.0's depreciated "packed" polygon icon definitions, 
to a simple raw bitmap (used by MicroHydra 2.0)
"""

from PIL import Image, ImageDraw

import os
import argparse


# argparser stuff:
PARSER = argparse.ArgumentParser(
prog='polygon_to_raw_bmp',
description="""\
Convert depreciated MicroHydra polygon defs into raw bitmaps.
""",
epilog='''MicroHydra 1.0 used packed polygons for custom launcher icons.
MicroHydra 2.0 uses raw bitmaps for this, and this tool is meant to make that transition simpler.'''
)

PARSER.add_argument('-f', '--input_file', help='Path to __icon__.txt (or similar) polygon file.')
PARSER.add_argument('-s', '--input_string', help='String containing packed polygon.')
PARSER.add_argument('-o', '--output_file', help='Output file name.')
SCRIPT_ARGS = PARSER.parse_args()

INPUT_FILE = SCRIPT_ARGS.input_file
INPUT_STRING = SCRIPT_ARGS.input_string
OUTPUT_FILE = SCRIPT_ARGS.output_file


# set defaults for args not given:
CWD = os.getcwd()

if INPUT_FILE is None:
    INPUT_FILE = os.path.join(CWD, '__icon__.txt')
if INPUT_STRING is None:
    with open(INPUT_FILE, 'r') as f:
        INPUT_STRING = f.read()

if OUTPUT_FILE is None:
    OUTPUT_FILE = os.path.join(CWD, 'icon.raw')    


# initial config: 

WIDTH = 32
HEIGHT = 32

CONFIG = {'ui_color':1, 'bg_color':0}

IMAGE = Image.new(mode='1', size=(WIDTH,HEIGHT), color=1)

DRAW = ImageDraw.Draw(IMAGE)



def unpack_shape(string):
    # this weird little function takes the memory-efficient 'packed' shape definition, and unpacks it to a valid arg tuple for DISPLAY.polygon
    unpacked = (
        "shape="
        + string.replace(
            'u', "),CONFIG['ui_color']"
        ).replace(
            'b', "),CONFIG['bg_color']"
        ).replace(
            'a', "(("
        ).replace(
            't', ',True)'
        ).replace(
            'f', ',False)'
        )
    )
    loc = {}
    exec(unpacked, globals(), loc)
    return loc['shape']
    


def polygon(shape):
    coords, clr, fill = shape

    # convert for PIL
    xy = []
    for i in range(0, len(coords), 2):
        x = coords[i]
        y = coords[i+1]
        xy.append((x,y))

    if fill:
        fill=clr
        outline=None
    else:
        fill=None
        outline=clr
    DRAW.polygon(xy, fill=fill, outline=outline)

# fill bg
DRAW.rectangle((0,0,32,32), fill=CONFIG['bg_color'])

# unpack and draw polygons
shapes = unpack_shape(INPUT_STRING)
for shape in shapes:
    polygon(shape)

# write output file
with open(OUTPUT_FILE, 'wb') as f:
    f.write(IMAGE.tobytes())
