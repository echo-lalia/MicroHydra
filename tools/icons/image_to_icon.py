"""
This tool converts an image (any that can be opened by PIL) into a MicroHydra icon,
in the form of a 32*32 raw bitmap
"""

from PIL import Image, ImageOps

import os
import argparse


# argparser stuff:
PARSER = argparse.ArgumentParser(
prog='image_to_icon',
description="""\
Convert an image into a MicroHydra icon file.
"""
)


PARSER.add_argument('input_image', help='Path to the image file.')
PARSER.add_argument('-o', '--output_file', help='Output file name (defaults to "icon.raw")')
PARSER.add_argument('-i', '--invert', help='Invert the image.', action='store_true')
PARSER.add_argument('-d', '--dither', help='Dither the converted image.', action='store_true')
PARSER.add_argument('-c', '--crop', help='Crop image before scaling.', action='store_true')
PARSER.add_argument('-p', '--preview', help='Open a preview of the converted image.', action='store_true')
SCRIPT_ARGS = PARSER.parse_args()


INPUT_IMAGE = SCRIPT_ARGS.input_image
OUTPUT_FILE = SCRIPT_ARGS.output_file


# set defaults for args not given:
CWD = os.getcwd()

if OUTPUT_FILE is None:
    OUTPUT_FILE = os.path.join(CWD, 'icon.raw')



WIDTH = 32
HEIGHT = 32

IMAGE = Image.open(INPUT_IMAGE)


if SCRIPT_ARGS.crop:
    target_size = min(IMAGE.width, IMAGE.height)
    w_crop = (IMAGE.width - target_size) // 2
    h_crop = (IMAGE.height - target_size) // 2
    IMAGE = IMAGE.crop((w_crop, h_crop, IMAGE.width - w_crop, IMAGE.height - h_crop))

IMAGE = IMAGE.resize((32, 32))


OUTPUT_IMAGE = IMAGE.convert('1', dither=SCRIPT_ARGS.dither)

if SCRIPT_ARGS.invert:
    OUTPUT_IMAGE = ImageOps.invert(OUTPUT_IMAGE)




# write output file
with open(OUTPUT_FILE, 'wb') as f:
    f.write(OUTPUT_IMAGE.tobytes())
    print(len(OUTPUT_IMAGE.tobytes()))

if  SCRIPT_ARGS.preview:
    PREVIEW = OUTPUT_IMAGE.resize((64,64))
    PREVIEW.show()
