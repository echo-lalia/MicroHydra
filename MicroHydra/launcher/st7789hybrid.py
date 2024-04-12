"""
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

The driver is based on st7789py and st7789fbuf (which can be found in the MicroHydra lib)
It has been modified for optimal use with MicroHydra launcher, and has been trimmed significantly. 
"""

import math, time, framebuf, struct

# ST7789 commands
# _ST7789_SWRESET = b"\x01"
_ST7789_SLPIN = b"\x10"
_ST7789_SLPOUT = b"\x11"
# _ST7789_NORON = b"\x13"
# _ST7789_INVOFF = b"\x20"
# _ST7789_INVON = b"\x21"
# _ST7789_DISPOFF = b"\x28"
# _ST7789_DISPON = b"\x29"
_ST7789_CASET = b"\x2a"
_ST7789_RASET = b"\x2b"
_ST7789_RAMWR = b"\x2c"
_ST7789_VSCRDEF = b"\x33"
# _ST7789_COLMOD = b"\x3a"
_ST7789_MADCTL = b"\x36"
# _ST7789_VSCSAD = b"\x37"
# _ST7789_RAMCTL = b"\xb0"
# _ST7789_PTLON = 0x12
# MADCTL bits
# _ST7789_MADCTL_MY = const(0x80)
# _ST7789_MADCTL_MX = const(0x40)
# _ST7789_MADCTL_MV = const(0x20)
# _ST7789_MADCTL_ML = const(0x10)
_ST7789_MADCTL_BGR = const(0x08)
# _ST7789_MADCTL_MH = const(0x04)
# _ST7789_MADCTL_RGB = const(0x00)

# RGB = 0x00
BGR = 0x08

# Color modes
# _COLOR_MODE_65K = const(0x50)
# _COLOR_MODE_262K = const(0x60)
# _COLOR_MODE_12BIT = const(0x03)
# _COLOR_MODE_16BIT = const(0x05)
# _COLOR_MODE_18BIT = const(0x06)
# _COLOR_MODE_16M = const(0x07)

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

#   (madctl, width, height, xstart, ystart, needs_swap)[rotation % 4]

_DISPLAY_135x240 = const((
    (0x00, 135, 240, 52, 40, False),
    (0x60, 240, 135, 40, 53, False),
    (0xc0, 135, 240, 53, 40, False),
    (0xa0, 240, 135, 40, 52, False)))

# # index values into rotation table
# _WIDTH = const(0)
# _HEIGHT = const(1)
# _XSTART = const(2)
# _YSTART = const(3)
# _NEEDS_SWAP = const(4)

# Supported displays (physical width, physical height, rotation table)
_SUPPORTED_DISPLAYS = ((135, 240, _DISPLAY_135x240),)

# init tuple format (b'command', b'data', delay_ms)
_ST7789_INIT_CMDS = (
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
    ( b'\x29', b'\x00', 120),                # Turn on the display
)

def swap_bytes(color):
    """
    this just flips the left and right byte in the 16 bit color.
    """
    return ((color & 0xff) << 0x8) + (color >> 0x8) 

class ST7789:
    """
    ST7789 driver class

    Args:
        spi (spi): spi object **Required**
        width (int): display width **Required**
        height (int): display height **Required**
        reset (pin): reset pin
        dc (pin): dc pin **Required**
        cs (pin): cs pin
        backlight(pin): backlight pin
        rotation (int):

          - 0-Portrait
          - 1-Landscape
          - 2-Inverted Portrait
          - 3-Inverted Landscape

        color_order (int):

          - RGB: Red, Green Blue, default
          - BGR: Blue, Green, Red

        custom_init (tuple): custom initialization commands

          - ((b'command', b'data', delay_ms), ...)

        custom_rotations (tuple): custom rotation definitions

          - ((width, height, xstart, ystart, madctl, needs_swap), ...)

    """

    def __init__(
        self,
        spi,
        width,
        height,
        reset=None,
        dc=None,
        cs=None,
        backlight=None,
        rotation=0,
        color_order=BGR,
        custom_init=None,
        custom_rotations=None,
    ):
        """
        Initialize display.
        """
        self.rotations = custom_rotations or self._find_rotations(width, height)
        if not self.rotations:
            supported_displays = ", ".join(
                [f"{display[0]}x{display[1]}" for display in _SUPPORTED_DISPLAYS]
            )
            raise ValueError(
                f"Unsupported {width}x{height} display. Supported displays: {supported_displays}"
            )

        if dc is None:
            raise ValueError("dc pin is required.")

        self.width = width
        self.height = height
        self.min_x = 0
        self.max_x = width
        
        self.xstart = 0
        self.ystart = 0
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        self._rotation = rotation % 4
        self.color_order = color_order
        self.init_cmds = custom_init or _ST7789_INIT_CMDS
        self.hard_reset()
        # yes, twice, once is not always enough
        self.init(self.init_cmds)
        self.init(self.init_cmds)
        self.rotation(self._rotation)
        self.needs_swap = False
        self.fill(0x0)

        if backlight is not None:
            backlight.value(1)

    @staticmethod
    def _find_rotations(width, height):
        for display in _SUPPORTED_DISPLAYS:
            if display[0] == width and display[1] == height:
                return display[2]
        return None

    def init(self, commands):
        """
        Initialize display.
        """
        for command, data, delay in commands:
            self._write(command, data)
            time.sleep_ms(delay)

    def _write(self, command=None, data=None):
        """SPI write to the device: commands and data."""
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

    def hard_reset(self):
        """
        Hard reset display.
        """
        if self.cs:
            self.cs.off()
        if self.reset:
            self.reset.on()
        time.sleep_ms(10)
        if self.reset:
            self.reset.off()
        time.sleep_ms(10)
        if self.reset:
            self.reset.on()
        time.sleep_ms(120)
        if self.cs:
            self.cs.on()

#     def soft_reset(self):
#         """
#         Soft reset display.
#         """
#         self._write(_ST7789_SWRESET)
#         time.sleep_ms(150)

    def sleep_mode(self, value):
        """
        Enable or disable display sleep mode.

        Args:
            value (bool): if True enable sleep mode. if False disable sleep
            mode
        """
        if value:
            self._write(_ST7789_SLPIN)
        else:
            self._write(_ST7789_SLPOUT)

#     def inversion_mode(self, value):
#         """
#         Enable or disable display inversion mode.
# 
#         Args:
#             value (bool): if True enable inversion mode. if False disable
#             inversion mode
#         """
#         if value:
#             self._write(_ST7789_INVON)
#         else:
#             self._write(_ST7789_INVOFF)

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
            self.needs_swap,
        ) = self.rotations[rotation]

        if self.color_order == BGR:
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
        #if x0 <= x1 <= self.width and y0 <= y1 <= self.height:
        self._write(
            _ST7789_CASET,
            struct.pack(_ENCODE_POS, x0 + self.xstart, x1 + self.xstart),
        )
        self._write(
            _ST7789_RASET,
            struct.pack(_ENCODE_POS, y0 + self.ystart, y1 + self.ystart),
        )
        self._write(_ST7789_RAMWR)

#     def vline(self, x, y, length, color):
#         """
#         Draw vertical line at the given location and color.
# 
#         Args:
#             x (int): x coordinate
#             Y (int): y coordinate
#             length (int): length of line
#             color (int): 565 encoded color
#         """
#         self.fill_rect(x, y, 1, length, color)

    def hline(self, x, y, length, color):
        """
        Draw horizontal line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self.fill_rect(x, y, length, 1, color)

#     def pixel(self, x, y, color):
#         """
#         Draw a pixel at the given location and color.
# 
#         Args:
#             x (int): x coordinate
#             Y (int): y coordinate
#             color (int): 565 encoded color
#         """
#         self._set_window(x, y, x, y)
#         self._write(
#             None,
#             struct.pack(
#                 _ENCODE_PIXEL_SWAPPED if self.needs_swap else _ENCODE_PIXEL, color
#             ),
#         )
        
    def fbuf_blit(self, buffer, fbuf, x, y, width, height, key=-1, palette=None):
        """
        Copy buffer to display framebuf at the given location.

        Args:
            buffer (bytes): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
            key (int): color to be considered transparent
            palette (framebuf): the color pallete to use for the buffer
        """
        fbuf.blit(framebuf.FrameBuffer(buffer,width, height, framebuf.RGB565), x,y,key,palette)
        
    def blit_buffer(self, buffer, x, y, width, height):
        """
        Copy buffer to display at the given location.

        Args:
            buffer (bytes): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
        """
        x_end = x + width - 1
        y_end = y + width - 1
        
        if x_end > self.max_x or x_end < self.min_x:
            return
        
        self._set_window(x, y, x_end, y_end)
        self._write(None, buffer)

#     def rect(self, x, y, w, h, color):
#         """
#         Draw a rectangle at the given location, size and color.
# 
#         Args:
#             x (int): Top left corner x coordinate
#             y (int): Top left corner y coordinate
#             width (int): Width in pixels
#             height (int): Height in pixels
#             color (int): 565 encoded color
#         """
#         self.hline(x, y, w, color)
#         self.vline(x, y, h, color)
#         self.vline(x + w - 1, y, h, color)
#         self.hline(x, y + h - 1, w, color)

    def fill_rect(self, x, y, width, height, color):
        """
        Draw a rectangle at the given location, size and filled with color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self._set_window(x, y, x + width - 1, y + height - 1)
        chunks, rest = divmod(width * height, _BUFFER_SIZE)
        pixel = struct.pack(
            _ENCODE_PIXEL_SWAPPED if self.needs_swap else _ENCODE_PIXEL, color
        )
        self.dc.on()
        if chunks:
            data = pixel * _BUFFER_SIZE
            for _ in range(chunks):
                self._write(None, data)
        if rest:
            self._write(None, pixel * rest)

    def fill(self, color, fbuf=None):
        """
        Args:
            color (int): 565 encoded color
        """
        if fbuf:
            color = swap_bytes(color)
            fbuf.fill(color)
        else:
            self.fill_rect(0, 0, self.width, self.height, color)

#     def line(self, x0, y0, x1, y1, color):
#         """
#         Draw a single pixel wide line starting at x0, y0 and ending at x1, y1.
# 
#         Args:
#             x0 (int): Start point x coordinate
#             y0 (int): Start point y coordinate
#             x1 (int): End point x coordinate
#             y1 (int): End point y coordinate
#             color (int): 565 encoded color
#         """
#         steep = abs(y1 - y0) > abs(x1 - x0)
#         if steep:
#             x0, y0 = y0, x0
#             x1, y1 = y1, x1
#         if x0 > x1:
#             x0, x1 = x1, x0
#             y0, y1 = y1, y0
#         dx = x1 - x0
#         dy = abs(y1 - y0)
#         err = dx // 2
#         ystep = 1 if y0 < y1 else -1
#         while x0 <= x1:
#             if steep:
#                 self.pixel(y0, x0, color)
#             else:
#                 self.pixel(x0, y0, color)
#             err -= dy
#             if err < 0:
#                 y0 += ystep
#                 err += dx
#             x0 += 1
# 
    def vscrdef(self, tfa, vsa, bfa):
        """
        Set Vertical Scrolling Definition.

        To scroll a 135x240 display these values should be 40, 240, 40.
        There are 40 lines above the display that are not shown followed by
        240 lines that are shown followed by 40 more lines that are not shown.
        You could write to these areas off display and scroll them into view by
        changing the TFA, VSA and BFA values.

        Args:
            tfa (int): Top Fixed Area
            vsa (int): Vertical Scrolling Area
            bfa (int): Bottom Fixed Area
        """
        self.width = tfa + vsa + bfa
        self.min_x = 0 - tfa
        self.max_x = vsa + bfa
        self._write(_ST7789_VSCRDEF, struct.pack(">HHH", tfa, vsa, bfa))

#     def vscsad(self, vssa):
#         """
#         Set Vertical Scroll Start Address of RAM.
# 
#         Defines which line in the Frame Memory will be written as the first
#         line after the last line of the Top Fixed Area on the display
# 
#         Example:
# 
#             for line in range(40, 280, 1):
#                 tft.vscsad(line)
#                 utime.sleep(0.01)
# 
#         Args:
#             vssa (int): Vertical Scrolling Start Address
# 
#         """
#         self._write(_ST7789_VSCSAD, struct.pack(">H", vssa))

    @micropython.viper
    @staticmethod
    def _pack8(glyphs, idx: uint, fg_color: uint, bg_color: uint):
        buffer = bytearray(128)
        bitmap = ptr16(buffer)
        glyph = ptr8(glyphs)

        for i in range(0, 64, 8):
            byte = glyph[idx]
            bitmap[i] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 1] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 2] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 3] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 4] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 5] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 6] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 7] = fg_color if byte & _BIT0 else bg_color
            idx += 1

        return buffer

    @micropython.viper
    @staticmethod
    def _pack16(glyphs, idx: uint, fg_color: uint, bg_color: uint):
        """
        Pack a character into a byte array.

        Args:
            char (str): character to pack

        Returns:
            128 bytes: character bitmap in color565 format
        """

        buffer = bytearray(256)
        bitmap = ptr16(buffer)
        glyph = ptr8(glyphs)

        for i in range(0, 128, 16):
            byte = glyph[idx]

            bitmap[i] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 1] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 2] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 3] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 4] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 5] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 6] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 7] = fg_color if byte & _BIT0 else bg_color
            idx += 1

            byte = glyph[idx]
            bitmap[i + 8] = fg_color if byte & _BIT7 else bg_color
            bitmap[i + 9] = fg_color if byte & _BIT6 else bg_color
            bitmap[i + 10] = fg_color if byte & _BIT5 else bg_color
            bitmap[i + 11] = fg_color if byte & _BIT4 else bg_color
            bitmap[i + 12] = fg_color if byte & _BIT3 else bg_color
            bitmap[i + 13] = fg_color if byte & _BIT2 else bg_color
            bitmap[i + 14] = fg_color if byte & _BIT1 else bg_color
            bitmap[i + 15] = fg_color if byte & _BIT0 else bg_color
            idx += 1

        return buffer

    def text(self, font, text, x0, y0, fg_color=65535, bg_color=0):
        """
        Internal method to write characters with width of 8 and
        heights of 8 or 16.

        Args:
            font (module): font module to use
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
            background (int): 565 encoded color to use for background
        """
        fg_color = swap_bytes(fg_color)
        bg_color = swap_bytes(bg_color)
        
        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
            ):
                if font.HEIGHT == 8:
                    passes = 1
                    size = 8
                    each = 0
                else:
                    passes = 2
                    size = 16
                    each = 8

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = self._pack8(font.FONT, idx, fg_color, bg_color)
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 8, 8)

                x0 += 8

    def fbuf_bitmap_text(self, font, fbuf, text, x0, y0, fg_color=65535):
        """
        Internal method to draw characters with width of 16 and heights of 16
        or 32.

        Args:
            font (module): font module to use
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
        """
        
        fg_color = swap_bytes(fg_color)
        
        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 <= self.width
                and y0 <= self.height
            ):
                each = 16
                if font.HEIGHT == 16:
                    passes = 2
                    size = 32
                else:
                    passes = 4
                    size = 64

                for line in range(passes):
                    idx = (ch - font.FIRST) * size + (each * line)
                    buffer = self._pack16(font.FONT, idx, fg_color, 0)
                    self.fbuf_blit(buffer, fbuf, x0, y0 + 8 * line, 16, 8,key=0)
            x0 += 16
            

    def bitmap_icons(self, bitmap_module, bitmap, palette, x, y, fbuf=None):
        """
        Draw a 2 color bitmap as a transparent icon on display,
        at the specified column and row, using given color and memoryview object.
        
        This function was particularly designed for use with MicroHydra Launcher,
        but could probably be useful elsewhere too.

        Args:
            (bitmap_module): The module containing the bitmap to draw
            bitmap: The actual bitmap buffer to draw
            color: the non-transparent color of the bitmap
            x (int): column to start drawing at
            y (int): row to start drawing at
            invert_colors (bool): flip transparent and non-tranparent parts of bitmap.
            
        """
        width = bitmap_module.WIDTH
        height = bitmap_module.HEIGHT
        to_col = x + width - 1
        to_row = y + height - 1
        if not fbuf and (self.width <= to_col or self.height <= to_row):
            return

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = bitmap_module.BPP
        bs_bit = 0
        needs_swap = self.needs_swap
        buffer = bytearray(buffer_len)
        
        if fbuf:
            palette = (0, swap_bytes(palette[1]))
        else:
            palette = (swap_bytes(palette[0]), swap_bytes(palette[1]))

        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (bitmap[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1

            color = palette[color_index]

            buffer[i] = color & 0xFF
            buffer[i + 1] = color >> 8

        if fbuf:
            self.fbuf_blit(buffer, fbuf, x, y, width, height, key=0)
        else:
            self._set_window(x, y, to_col, to_row)
            self._write(None, buffer)

                
                
    def polygon(self,x,y,points,color,fill, fbuf=None):
        """
        Draw a polygon on the display.

        Args:
            points (array('h')): Array of points to draw.
            x (int): X-coordinate of the polygon's position.
            y (int): Y-coordinate of the polygon's position.
            color (int): 565 encoded color.
        """
        color = swap_bytes(color)
        fbuf.poly(x,y,points,color,fill)