#!/usr/bin/env python3

"""
Convert a sprite sheet image to python a module for use with indexed bitmap method. The Sprite sheet
width and height should be a multiple of sprite width and height. There should be no extra pixels
between sprites. All sprites will share the same palette.

.. seealso::
    - :ref:`tiny_toasters.py<tiny_toasters>`.

Example
^^^^^^^

.. code-block:: console

    # create a sprite sheet with 7 colored sprites 32x32 pixels each
    ./make_colorbars_bitmap.py 227 32 3 --png sprites.png

    # convert the sprite sheet to a python module with 7 sprites
    ./sprites_converter.py sprites.png 32 32 4 > sprites.py

.. code-block:: python

    import tft_config
    import sprites
    tft = tft_config.config(1)
    for i in range(sprites.BITMAPS):
        tft.bitmap(sprites, 0, 0, i)

Usage
^^^^^

.. code-block:: console

    usage: sprites_converter.py [-h] image_file sprite_width sprite_height bits_per_pixel

    Convert image file to python module for use with bitmap method.

    positional arguments:
    image_file      Name of file containing image to convert
    sprite_width    Width of sprites in pixels
    sprite_height   Height of sprites in pixels
    bits_per_pixel  The number of bits to use per pixel (1..8)

    optional arguments:
    -h, --help      show this help message and exit



This script was originally written by Russ Hughes as part of the 'st7789py_mpy' repo.


MIT License

Copyright (c) 2020-2023 Russ Hughes

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import argparse
from PIL import Image


def convert_image_to_bitmap(image_file, bits, sprite_width, sprite_height):
    """
    Convert image to bitmap representation.

    Args:
        img (PIL.Image.Image): Image object to convert.
        bits (int): The number of bits to use per pixel (1..8).
        sprite_width (int): Width of sprites in pixels.
        sprite_height (int): Height of sprites in pixels.

    Returns:
        tuple: Tuple containing the bitmap parameters and the bitmap data.

    Raises:
        None
    """
    colors_requested = 1 << bits
    img = Image.open(image_file).convert("RGB")
    img = img.convert(mode="P", palette=Image.Palette.ADAPTIVE, colors=colors_requested)

    palette = img.getpalette()
    palette_colors = len(palette) // 3
    actual_colors = min(palette_colors, colors_requested)

    colors = []
    for color in range(actual_colors):
        color565 = (
            ((palette[color * 3] & 0xF8) << 8)
            | ((palette[color * 3 + 1] & 0xFC) << 3)
            | ((palette[color * 3 + 2] & 0xF8) >> 3)
        )
        colors.append(f"{color565:04x}")

    image_bitstring = ""
    bitmaps = 0

    sprite_cols = img.width // sprite_width
    width_of_sprites = sprite_cols * sprite_width
    sprite_rows = img.height // sprite_height
    height_of_sprites = sprite_rows * sprite_height

    for y in range(0, height_of_sprites, sprite_height):
        for x in range(0, width_of_sprites, sprite_width):
            bitmaps += 1
            for yy in range(y, y + sprite_height):
                for xx in range(x, x + sprite_width):
                    try:
                        pixel = img.getpixel((xx, yy))
                    except IndexError:
                        print(
                            f"IndexError: xx={xx}, yy={yy} check your sprite width and height",
                            file=sys.stderr,
                        )
                        pixel = 0
                    color = pixel
                    image_bitstring += "".join(
                        "1" if (color & (1 << bit - 1)) else "0"
                        for bit in range(bits, 0, -1)
                    )

    bitmap_bits = len(image_bitstring)

    # Create python source with image parameters
    print(f"BITMAPS = {bitmaps}")
    print(f"HEIGHT = {sprite_height}")
    print(f"WIDTH = {sprite_width}")
    print(f"COLORS = {actual_colors}")
    print(f"BITS = {bitmap_bits}")
    print(f"BPP = {bits}")
    print("PALETTE = [", sep="", end="")

    for color, rgb in enumerate(colors):
        if color:
            print(",", sep="", end="")
        print(f"0x{rgb}", sep="", end="")
    print("]")

    # Run though image bit string 8 bits at a time
    # and create python array source for memoryview

    print("_bitmap =\\", sep="")
    print("b'", sep="", end="")

    for i in range(0, bitmap_bits, 8):
        if i and i % (16 * 8) == 0:
            print("'\\\nb'", end="", sep="")

        value = image_bitstring[i : i + 8]
        color = int(value, 2)
        print(f"\\x{color:02x}", sep="", end="")

    print("'\nBITMAP = memoryview(_bitmap)")


def main():
    """
    Convert images to python modules for use with indexed bitmap method.

    Args:
        input (str): image file to convert.
        sprite_width (int): Width of sprites in pixels.
        sprite_height (int): Height of sprites in pixels.
        bits_per_pixel (int): The number of color bits to use per pixel (1..8).

    """

    parser = argparse.ArgumentParser(
        description="Convert image file to python module for use with bitmap method.",
    )

    parser.add_argument("image_file", help="Name of file containing image to convert")
    parser.add_argument("sprite_width", type=int, help="Width of sprites in pixels")
    parser.add_argument("sprite_height", type=int, help="Height of sprites in pixels")

    parser.add_argument(
        "bits_per_pixel",
        type=int,
        choices=range(1, 9),
        default=1,
        metavar="bits_per_pixel",
        help="The number of bits to use per pixel (1..8)",
    )

    args = parser.parse_args()

    convert_image_to_bitmap(
        args.image_file, args.bits_per_pixel, args.sprite_width, args.sprite_height
    )


main()
