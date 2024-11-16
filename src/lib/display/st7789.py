"""A ST7789 display driver.

MIT License

Copyright (c) 2024 Ethan Lacasse

Copyright (c) 2020-2023 Russ Hughes

Copyright (c) 2019 Ivan Belokobylskiy

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

The driver is based on russhughes' st7789py_mpy module from
https://github.com/russhughes/st7789py_mpy, which is based on
https://github.com/devbis/st7789py_mpy.

This driver has been modified to use the fast MicroPython framebuf module as much as possible.
Specifically, it has been made for MicroHydra.

This module will use a lot more ram than the original, but it should be much faster too.

This driver supports:

- 320x240, 240x240, 135x240 and 128x128 pixel displays
- Display rotation
- RGB and BGR color orders
"""

import struct
from time import sleep_ms

import framebuf

from .palette import Palette
from .displaycore import DisplayCore


# mh_if frozen:
# # frozen firmware must access the font as a module,
# # rather than a binary file.
# from font.utf8_8x8 import utf8
# mh_end_if


_MH_DISPLAY_BAUDRATE = const(40_000_000)


# ST7789 commands
_ST7789_SWRESET = b"\x01"
_ST7789_SLPIN = b"\x10"
_ST7789_SLPOUT = b"\x11"
_ST7789_NORON = b"\x13"
_ST7789_INVOFF = b"\x20"
_ST7789_INVON = b"\x21"
_ST7789_DISPOFF = b"\x28"
_ST7789_DISPON = b"\x29"
_ST7789_CASET = b"\x2a"
_ST7789_RASET = b"\x2b"
_ST7789_RAMWR = b"\x2c"
_ST7789_VSCRDEF = b"\x33"
_ST7789_COLMOD = b"\x3a"
_ST7789_MADCTL = b"\x36"
_ST7789_VSCSAD = b"\x37"
_ST7789_RAMCTL = b"\xb0"

# MADCTL bits
_ST7789_MADCTL_MY = const(0x80)
_ST7789_MADCTL_MX = const(0x40)
_ST7789_MADCTL_MV = const(0x20)
_ST7789_MADCTL_ML = const(0x10)
_ST7789_MADCTL_BGR = const(0x08)
_ST7789_MADCTL_MH = const(0x04)
_ST7789_MADCTL_RGB = const(0x00)

_RGB = const(0x00)
_BGR = const(0x08)

# Color modes
_COLOR_MODE_65K = const(0x50)
_COLOR_MODE_262K = const(0x60)
_COLOR_MODE_12BIT = const(0x03)
_COLOR_MODE_16BIT = const(0x05)
_COLOR_MODE_18BIT = const(0x06)
_COLOR_MODE_16M = const(0x07)


_ENCODE_PIXEL = const(">H")
_ENCODE_PIXEL_SWAPPED = const("<H")
_ENCODE_POS = const(">HH")
_ENCODE_POS_16 = const("<HH")

# must be at least 128 for 8 bit wide fonts
# must be at least 256 for 16 bit wide fonts
_BUFFER_SIZE = const(256)

_BIT7 = const(0x80)
_BIT6 = const(0x40)
_BIT5 = const(0x20)
_BIT4 = const(0x10)
_BIT3 = const(0x08)
_BIT2 = const(0x04)
_BIT1 = const(0x02)
_BIT0 = const(0x01)

# fmt: off

# Rotation tables
#   (madctl, width, height, xstart, ystart)[rotation % 4]

_DISPLAY_240x320 = const((
    (0x00, 240, 320, 0, 0),
    (0x60, 320, 240, 0, 0),
    (0xc0, 240, 320, 0, 0),
    (0xa0, 320, 240, 0, 0)))

_DISPLAY_240x240 = const((
    (0x00, 240, 240,  0,  0),
    (0x60, 240, 240,  0,  0),
    (0xc0, 240, 240,  0, 80),
    (0xa0, 240, 240, 80,  0)))

_DISPLAY_135x240 = const((
    (0x00, 135, 240, 52, 40),
    (0x60, 240, 135, 40, 53),
    (0xc0, 135, 240, 53, 40),
    (0xa0, 240, 135, 40, 52)))

_DISPLAY_128x128 = const((
    (0x00, 128, 128, 2, 1),
    (0x60, 128, 128, 1, 2),
    (0xc0, 128, 128, 2, 1),
    (0xa0, 128, 128, 1, 2)))

# Supported displays (physical width, physical height, rotation table)
_SUPPORTED_DISPLAYS = const((
    (240, 320, _DISPLAY_240x320),
    (240, 240, _DISPLAY_240x240),
    (135, 240, _DISPLAY_135x240),
    (128, 128, _DISPLAY_128x128)))

# init tuple format (b'command', b'data', delay_ms)
_ST7789_INIT_CMDS = const((
    ( b'\x11', b'\x00', 120),               # Exit sleep mode
    ( b'\x13', b'\x00', 0),                 # Turn on the display
    ( b'\xb6', b'\x0a\x82', 0),             # Set display function control
    ( b'\x3a', b'\x55', 10),                # Set pixel format to 16 bits per pixel (RGB565)
    ( b'\xb2', b'\x0c\x0c\x00\x33\x33', 0), # Set porch control
    ( b'\xb7', b'\x35', 0),                 # Set gate control
    ( b'\xbb', b'\x28', 0),                 # Set VCOMS setting
    ( b'\xc0', b'\x0c', 0),                 # Set power control 1
    ( b'\xc2', b'\x01\xff', 0),             # Set power control 2
    ( b'\xc3', b'\x10', 0),                 # Set power control 3
    ( b'\xc4', b'\x20', 0),                 # Set power control 4
    ( b'\xc6', b'\x0f', 0),                 # Set VCOM control 1
    ( b'\xd0', b'\xa4\xa1', 0),             # Set power control A
                                            # Set gamma curve positive polarity
    ( b'\xe0', b'\xd0\x00\x02\x07\x0a\x28\x32\x44\x42\x06\x0e\x12\x14\x17', 0),
                                            # Set gamma curve negative polarity
    ( b'\xe1', b'\xd0\x00\x02\x07\x0a\x28\x31\x54\x47\x0e\x1c\x17\x1b\x1e', 0),
    ( b'\x21', b'\x00', 0),                 # Enable display inversion
    ( b'\x29', b'\x00', 120)                # Turn on the display
))

# fmt: on



class ST7789(DisplayCore):
    """ST7789 driver class."""

    def __init__(
            self,
            spi,
            width,
            height,
            *,
            reset=None,
            dc=None,
            cs=None,
            rotation=0,
            color_order='BGR',
            **kwargs):
        """Initialize display.

        Args:
            spi (spi): spi object **Required**
            width (int): display width **Required**
            height (int): display height **Required**
            reset (pin): reset pin
            dc (pin): dc pin **Required**
            cs (pin): cs pin

            rotation (int):
            - 0-Portrait
            - 1-Landscape
            - 2-Inverted Portrait
            - 3-Inverted Landscape

            color_order (literal['RGB'|'BGR']):
        """
        self.rotations = self._find_rotations(width, height)

        super().__init__(width, height, rotation=rotation, **kwargs)

        self.xstart = 0
        self.ystart = 0
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self._rotation = rotation % 4
        self.color_order = _RGB if color_order == "RGB" else _BGR
        self.hard_reset()
        # yes, twice, once is not always enough
        self.init(_ST7789_INIT_CMDS)
        self.init(_ST7789_INIT_CMDS)
        self.rotation(self._rotation)
        self.fill(0x0)
        self.show()
        if self.backlight:
            self.set_brightness(self.config['brightness'])

        # mh_if not frozen:
        # when not frozen, the utf8 font is read as needed from a binary.
        self.utf8_font = open("/font/utf8_8x8.bin", "rb", buffering = 0)  # noqa: SIM115
        # mh_end_if


    @staticmethod
    def _find_rotations(width: int, height: int) -> tuple:
        for display in _SUPPORTED_DISPLAYS:
            if display[0] == width and display[1] == height:
                return display[2]
        msg = f"{width}x{height} display. Not in `_SUPPORTED_DISPLAYS`"
        raise ValueError(msg)


    def init(self, commands: tuple):
        """Initialize display."""
        for command, data, delay in commands:
            self._write(command, data)
            sleep_ms(delay)


    def _write(self, command=None, data=None):
        """SPI write to the device: commands and data."""
        # mh_if shared_sdcard_spi:
        # # TDeck shares SPI with SDCard
        # self.spi.init(baudrate=_MH_DISPLAY_BAUDRATE)
        # mh_end_if
        if self.cs:
            self.cs.off()
        if command is not None:
            self.dc.off()
            self.spi.write(command)
        if data is not None:
            self.dc.on()
            self.spi.write(data)
        if self.cs:
            self.cs.on()


    @micropython.viper
    def _write_tiny_buf(self, y_min: int, y_max: int):
        """Convert tiny_buf data to RGB565 and write to SPI.

        This Viper method iterates over each line from y_min to y_max,
        converts the 4bit data to 16bit RGB565 format,
        and sends the data over SPI.
        """
        # mh_if shared_sdcard_spi:
        # # TDeck shares SPI with SDCard
        # self.spi.init(baudrate=_MH_DISPLAY_BAUDRATE)
        # mh_end_if
        if self.cs:
            self.cs.off()
        self.dc.on()

        width = int(self.width)
        start_y = int(y_min)
        end_y = int(y_max)

        # swap colors in palette if needed
        if self.needs_swap:
            palette_buf = bytearray(32)
            target_palette_ptr = ptr16(palette_buf)
            source_palette_ptr = ptr16(self.palette.buf)
            for i in range(16):
                target_palette_ptr[i] = ((source_palette_ptr[i] & 255) << 8) | (source_palette_ptr[i] >> 8)
        else:
            target_palette_ptr = ptr16(self.palette.buf)


        # prepare variables for line conversion loop:
        source_ptr = ptr8(self.fbuf)
        source_width = width // 2 if (width % 8 == 0) else ((width + 1) // 2)
        output_buf = bytearray(width * 2)
        output = ptr16(output_buf)

        # Iterate (vertically) over each horizontal line in given range:
        while start_y < end_y:
            source_start_idx = source_width * start_y
            output_idx = 0
            # Iterate over horizontal pixels:
            while output_idx < width:
                # Calculate source pixel location, and sample it.
                source_idx = source_start_idx + (output_idx // 2)
                sample = source_ptr[source_idx] >> 4 if (output_idx % 2 == 0) else source_ptr[source_idx] & 0xf

                output[output_idx] = target_palette_ptr[sample]
                output_idx += 1

            # Write buffer to SPI
            self.spi.write(output_buf)

            start_y += 1

        if self.cs:
            self.cs.on()


    def _write_normal_buf(self, y_min: int, y_max: int):
        """Write normal framebuf data, respecting show_y_min/max values."""
        source_start_idx = y_min * self.width * 2
        source_end_idx = y_max * self.width * 2

        if source_start_idx < source_end_idx:
            self._write(None, memoryview(self.fbuf)[source_start_idx:source_end_idx])


    def hard_reset(self):
        """Hard reset display."""
        if self.cs:
            self.cs.off()
        if self.reset:
            self.reset.on()
        sleep_ms(10)
        if self.reset:
            self.reset.off()
        sleep_ms(10)
        if self.reset:
            self.reset.on()
        sleep_ms(120)
        if self.cs:
            self.cs.on()


    def soft_reset(self):
        """Soft reset display."""
        self._write(_ST7789_SWRESET)
        sleep_ms(150)


    def sleep_mode(self, value: bool):
        """
        Enable or disable display sleep mode.

        Args:
            value (bool): if True enable sleep mode. if False disable sleep
            mode
        """
        # mh_if shared_sdcard_spi:
        # # TDeck shares SPI with SDCard
        # self.spi.init(baudrate=_MH_DISPLAY_BAUDRATE)
        # mh_end_if
        if value:
            self._write(_ST7789_SLPIN)
        else:
            self._write(_ST7789_SLPOUT)


    def inversion_mode(self, value: bool):
        """
        Enable or disable display inversion mode.

        Args:
            value (bool): if True enable inversion mode. if False disable
            inversion mode
        """
        # mh_if shared_sdcard_spi:
        # # TDeck shares SPI with SDCard
        # self.spi.init(baudrate=_MH_DISPLAY_BAUDRATE)
        # mh_end_if
        if value:
            self._write(_ST7789_INVON)
        else:
            self._write(_ST7789_INVOFF)


    def rotation(self, rotation):
        """
        Set display rotation.

        Args:
            rotation (int):
                - 0-Portrait
                - 1-Landscape
                - 2-Inverted Portrait
                - 3-Inverted Landscape

            custom_rotations can have any number of rotations
        """
        rotation %= len(self.rotations)
        self._rotation = rotation
        (
            madctl,
            self.width,
            self.height,
            self.xstart,
            self.ystart,
        ) = self.rotations[rotation]

        if self.color_order == _BGR:
            madctl |= _ST7789_MADCTL_BGR
        else:
            madctl &= ~_ST7789_MADCTL_BGR

        self._write(_ST7789_MADCTL, bytes([madctl]))


    def _set_window(self, x0, y0, x1, y1):
        """
        Set window to column and row address.

        Args:
            x0 (int): column start address
            y0 (int): row start address
            x1 (int): column end address
            y1 (int): row end address
        """
        if x0 <= x1 <= self.width and y0 <= y1 <= self.height:
            self._write(
                _ST7789_CASET,
                struct.pack(_ENCODE_POS, x0 + self.xstart, x1 + self.xstart),
            )
            self._write(
                _ST7789_RASET,
                struct.pack(_ENCODE_POS, y0 + self.ystart, y1 + self.ystart),
            )
            self._write(_ST7789_RAMWR)


    def show(self):
        """Write the current framebuf to the display."""
        # mh_if shared_sdcard_spi:
        # # TDeck shares SPI with SDCard
        # self.spi.init(baudrate=_MH_DISPLAY_BAUDRATE)
        # mh_end_if

        # Reset and clamp min/max vals
        y_min, y_max = self.reset_show_y()

        if y_min >= y_max:
            # nothing to show
            return

        self._set_window(
            0,
            y_min,
            self.width - 1,
            y_max - 1,
            )

        if self.use_tiny_buf:
            self._write_tiny_buf(y_min, y_max)
        else:
            self._write_normal_buf(y_min, y_max)
