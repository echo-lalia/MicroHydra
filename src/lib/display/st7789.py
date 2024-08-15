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
- Hardware based scrolling
- Drawing text using 8 and 16 bit wide bitmap fonts with heights that are
  multiples of 8.  Included are 12 bitmap fonts derived from classic pc
  BIOS text mode fonts.
- Drawing converted bitmaps
- Named color constants

  - BLACK
  - BLUE
  - RED
  - GREEN
  - CYAN
  - MAGENTA
  - YELLOW
  - WHITE

"""

from .palette import Palette
import framebuf, struct
from time import sleep_ms



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
#   (madctl, width, height, xstart, ystart, needs_swap)[rotation % 4]

_DISPLAY_240x320 = const((
    (0x00, 240, 320, 0, 0, False),
    (0x60, 320, 240, 0, 0, False),
    (0xc0, 240, 320, 0, 0, False),
    (0xa0, 320, 240, 0, 0, False)))

_DISPLAY_240x240 = const((
    (0x00, 240, 240,  0,  0, False),
    (0x60, 240, 240,  0,  0, False),
    (0xc0, 240, 240,  0, 80, False),
    (0xa0, 240, 240, 80,  0, False)))

_DISPLAY_135x240 = const((
    (0x00, 135, 240, 52, 40, False),
    (0x60, 240, 135, 40, 53, False),
    (0xc0, 135, 240, 53, 40, False),
    (0xa0, 240, 135, 40, 52, False)))

_DISPLAY_128x128 = const((
    (0x00, 128, 128, 2, 1, False),
    (0x60, 128, 128, 1, 2, False),
    (0xc0, 128, 128, 2, 1, False),
    (0xa0, 128, 128, 1, 2, False)))

# index values into rotation table
_WIDTH = const(0)
_HEIGHT = const(1)
_XSTART = const(2)
_YSTART = const(3)
_NEEDS_SWAP = const(4)

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

@micropython.viper
def color565(r:int, g:int, b:int) -> int:
    """
    Convert red, green and blue values (0-255) into a 16-bit 565 encoding.
    """
    r = (r * 31) // 255
    g = (g * 63) // 255
    b = (b * 31) // 255
    return (r << 11) | (g << 5) | b


@micropython.viper
def swap_bytes(color:int) -> int:
    """
    this just flips the left and right byte in the 16 bit color.
    """
    return ((color & 255) << 8) | (color >> 8)



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
        reserved_bytearray (bytearray): pre-allocated bytearray to use for framebuffer
        use_tiny_buf (bool):
            
            Whether to use:
             - A compact framebuffer (uses ~width * height / 2 bytes memory)
               "GS4_HMSB" mode
               Requires additional processing to write to display
               Allows limited colors

             - A normal framebuffer (uses ~width * height * 2 bytes memory)
               "RGB565" mode
               Can be written directly to display
               Allows any color the display can show
        
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
        color_order='BGR',
        custom_init=None,
        custom_rotations=None,
        reserved_bytearray = None,
        use_tiny_buf = False,
        **kwargs,
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
        
        #init the fbuf
        if reserved_bytearray is None:
            # use_tiny_fbuf tells us to use a smaller framebuffer (4 bits per pixel rather than 16 bits)
            if use_tiny_buf:
                # round width up to 8 bits
                size = (height * width) // 2 if (width % 8 == 0) else (height * (width + 1)) // 2
                reserved_bytearray = bytearray(size)

            else: # full sized buffer
                reserved_bytearray = bytearray(height*width*2)

        self.fbuf = framebuf.FrameBuffer(
            reserved_bytearray,
            # height and width are swapped when rotation is 1 or 3
            height if (rotation % 2 == 1) else width,
            width if (rotation % 2 == 1) else height,
            # use_tiny_fbuf uses GS4 format for less memory usage
            framebuf.GS4_HMSB if use_tiny_buf else framebuf.RGB565,
            )
        
        
        self.palette = Palette()
        self.palette.use_tiny_buf = self.use_tiny_buf = use_tiny_buf
        
        # keep track of min/max y vals for writing to display
        # this speeds up drawing significantly.
        # only y value is currently used, because framebuffer is stored in horizontal lines,
        # making y slices much simpler than x slices.
        self._show_y_min = width if (rotation % 2 == 1) else height
        self._show_y_max = 0
        
        self.width = width
        self.height = height
        self.xstart = 0
        self.ystart = 0
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        self._rotation = rotation % 4
        self.color_order = _RGB if color_order == "RGB" else _BGR
        init_cmds = custom_init or _ST7789_INIT_CMDS
        self.hard_reset()
        # yes, twice, once is not always enough
        self.init(init_cmds)
        self.init(init_cmds)
        self.rotation(self._rotation)
        self.needs_swap = True
        self.fill(0x0)
        self.show()

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
            sleep_ms(delay)


    def _reset_show_min(self):
        """Reset show boundaries"""
        self._show_y_min = self.height
        self._show_y_max = 0


    @micropython.viper
    def _set_show_min(self, y0:int, y1:int):
        """Set/store minimum and maximum Y to show next time show() is called."""
        y_min = int(self._show_y_min)
        y_max = int(self._show_y_max)
        
        
        if y_min > y0:
            y_min = y0
        if y_max < y1:
            y_max = y1

        self._show_y_min = y_min
        self._show_y_max = y_max

    
    @micropython.viper
    def _format_color(self, color:int) -> int:
        """Swap color bytes if needed, do nothing otherwise."""
        if (not self.use_tiny_buf) and self.needs_swap:
            color = ((color & 0xff) << 8) | (color >> 8)
        return color


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
    
    
    @micropython.viper
    def _write_tiny_buf(self):
        """Convert tiny_buf data to RGB565 and write to SPI"""
        if self.cs:
            self.cs.off()
        self.dc.on()
        
        landscape_rotation = int(self._rotation) % 2 == 1
        
        height = int(self.height)
        width = int(self.width)
        
        start_y = int(self._show_y_min)
        end_y = int(self._show_y_max)
        
        # swap colors if needed
        if self.needs_swap:
            palette_buf = bytearray(32)
            target_palette_ptr = ptr16(palette_buf)
            source_palette_ptr = ptr16(self.palette.buf)
            for i in range(16):
                target_palette_ptr[i] = ((source_palette_ptr[i] & 255) << 8) | (source_palette_ptr[i] >> 8)
        else:
            palette_buf = self.palette.buf
        
        #for y in range(start_y, end_y):
        while start_y < end_y:
            self.spi.write(
                self._convert_tiny_line(palette_buf, start_y, width)
                )
            start_y += 1
        
        if self.cs:
            self.cs.on()


    @micropython.viper
    def _convert_tiny_line(self, palette_buf, y:int, width:int):
        """
        For "_write_tiny_buf"
        this method outputs a single converted line of the requested size.
        """
        source_ptr = ptr8(self.fbuf)
        palette = ptr16(palette_buf)
        output_buf = bytearray(width * 2)
        output = ptr16(output_buf)
        
        
        source_width = width // 2 if (width % 8 == 0) else ((width + 1) // 2)
        source_start_idx = source_width * y
        output_idx = 0
        
        while output_idx < width:
            source_idx = source_start_idx + (output_idx // 2)
            sample = source_ptr[source_idx] >> 4 if (output_idx % 2 == 0) else source_ptr[source_idx] & 0xf

            output[output_idx] = palette[sample]
            
            output_idx += 1
        
        return output_buf


    def _write_normal_buf(self):
        """Write normal framebuf data, respecting show_y_min/max values."""
        source_start_idx = self._show_y_min * self.width * 2
        source_end_idx = self._show_y_max * self.width * 2
        
        self._write(None, memoryview(self.fbuf)[source_start_idx:source_end_idx])


    def hard_reset(self):
        """
        Hard reset display.
        """
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
        """
        Soft reset display.
        """
        self._write(_ST7789_SWRESET)
        sleep_ms(150)


    def sleep_mode(self, value):
        """
        Enable or disable display sleep mode.

        Args:
            value (bool): if True enable sleep mode. if False disable sleep
            mode
        """
        # mh_if TDECK:
        # TDeck shares SPI with SDCard
        self.spi.init()
        # mh_end_if
        if value:
            self._write(_ST7789_SLPIN)
        else:
            self._write(_ST7789_SLPOUT)
        # mh_if TDECK:
        self.spi.deinit()
        # mh_end_if


    def inversion_mode(self, value):
        """
        Enable or disable display inversion mode.

        Args:
            value (bool): if True enable inversion mode. if False disable
            inversion mode
        """
        # mh_if TDECK:
        # TDeck shares SPI with SDCard
        self.spi.init()
        # mh_end_if
        if value:
            self._write(_ST7789_INVON)
        else:
            self._write(_ST7789_INVOFF)
        # mh_if TDECK:
        self.spi.deinit()
        # mh_end_if


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


    def vline(self, x, y, length, color):
        """
        Draw vertical line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self._set_show_min(y, y + length)
        color = self._format_color(color)
        self.fbuf.vline(x, y, length, color)


    def hline(self, x, y, length, color):
        """
        Draw horizontal line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self._set_show_min(y, y)
        color = self._format_color(color)
        self.fbuf.hline(x, y, length, color)


    def pixel(self, x, y, color):
        """
        Draw a pixel at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            color (int): 565 encoded color
        """
        self._set_show_min(y, y)
        color = self._format_color(color)
        self.fbuf.pixel(x,y,color)
        
        
    def show(self):
        """
        Write the current framebuf to the display
        """
        if self._show_y_min > self._show_y_max:
            # nothing to show
            return
        
        # mh_if TDECK:
        # TDeck shares SPI with SDCard
        self.spi.init()
        # mh_end_if

        # clamp min and max
        if self._show_y_min < 0:
            self._show_y_min = 0
        if self._show_y_max > self.height:
            self._show_y_max = self.height
        
        self._set_window(
            0,
            self._show_y_min,
            self.width - 1,
            self._show_y_max - 1,
            )

        if self.use_tiny_buf:
            self._write_tiny_buf()
        else:
            self._write_normal_buf()
        
        self._reset_show_min()
        # mh_if TDECK:
        # TDeck shares SPI with SDCard
        self.spi.deinit()
        # mh_end_if
        
        
    def blit_buffer(self, buffer, x, y, width, height, key=-1, palette=None):
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
        self._set_show_min(y, y + height)
        if not isinstance(buffer, framebuf.FrameBuffer):
            buffer = framebuf.FrameBuffer(
                buffer, width, height,
                framebuf.GS4_HMSB if self.use_tiny_buf else framebuf.RGB565,
                )
        
        self.fbuf.blit(buffer, x, y, key, palette)


    def rect(self, x, y, w, h, color, fill=False):
        """
        Draw a rectangle at the given location, size and color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self._set_show_min(y, y + h)
        color = self._format_color(color)
        self.fbuf.rect(x,y,w,h,color,fill)


    def ellipse(self, x, y, xr, yr, color, fill=False, m=0xf):
        """
        Draw an ellipse at the given location, radius and color.

        Args:
            x (int): Center x coordinate
            y (int): Center y coordinate
            xr (int): x axis radius
            yr (int): y axis radius
            color (int): 565 encoded color
            fill (bool): fill in the ellipse. Default is False
        """
        self._set_show_min(y - yr, y + yr + 1)
        color = self._format_color(color)
        self.fbuf.ellipse(x,y,xr,yr,color,fill,m)


    def fill_rect(self, x, y, width, height, color):
        """
        Draw a rectangle at the given location, size and filled with color.
        
        This is just a wrapper for the rect() method,
        and is provided for compatibility with the original st7789py driver.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self._set_show_min(y, y + height)
        self.rect(x, y, width, height, color, fill=True)


    def fill(self, color):
        """
        Fill the entire FrameBuffer with the specified color.

        Args:
            color (int): 565 encoded color
        """
        # whole display must show
        self._set_show_min(0, self.height)
        color = self._format_color(color)
        self.fbuf.fill(color)


    def line(self, x0, y0, x1, y1, color):
        """
        Draw a single pixel wide line starting at x0, y0 and ending at x1, y1.

        Args:
            x0 (int): Start point x coordinate
            y0 (int): Start point y coordinate
            x1 (int): End point x coordinate
            y1 (int): End point y coordinate
            color (int): 565 encoded color
        """
        self._set_show_min(
            min(y0,y1),
            max(y0,y1)
            )
        color = self._format_color(color)
        self.fbuf.line(x0, y0, x1, y1, color)


    def scroll(self,xstep,ystep):
        """
        Shift the contents of the FrameBuffer by the given vector.
        This may leave a footprint of the previous colors in the FrameBuffer.

        Unlike vscsad which uses the hardware for scrolling,
        this method scrolls the framebuffer itself.
        This is a wrapper for the framebuffer.scroll method:
        """
        self._set_show_min(0, self.height)
        self.fbuf.scroll(xstep,ystep)


    @micropython.viper
    def _bitmap_text(self, font, text, x:int, y:int, color:int):
        """
        Internal viper method to draw text.
        Designed to be envoked using the 'text' method.

        Args:
            font (module): font module to use
            text (str): text to write
            x (int): column to start drawing at
            y (int): row to start drawing at
            color (int): encoded color to use for characters
        """
        width = int(font.WIDTH)
        height = int(font.HEIGHT)
        self_width = int(self.width)
        self_height = int(self.height)
        
        # early return for text off screen
        if y >= self_height or (y + height) < 0:
            return
        
        glyphs = ptr8(font.FONT)
        
        char_px_len = width * height
        
        first = int(font.FIRST)
        last = int(font.LAST)
        
        
        use_tiny_fbuf = bool(self.use_tiny_buf)
        fbuf16 = ptr16(self.fbuf)
        fbuf8 = ptr8(self.fbuf)
        
        for char in text:
            ch_idx = int(ord(char))
            
            # only draw chars that exist in font
            if first <= ch_idx < last:
                bit_start = (ch_idx - first) * char_px_len
                
                px_idx = 0
                while px_idx < char_px_len:
                    byte_idx = (px_idx + bit_start) // 8
                    shift_amount = 7 - ((px_idx + bit_start) % 8)
                    
                    target_x = x + px_idx % width
                    target_y = y + px_idx // width
                    
                    # dont draw pixels off the screen (ptrs don't check your work!)
                    if ((glyphs[byte_idx] >> shift_amount) & 0x1) == 1 \
                    and 0 <= target_x < self_width \
                    and 0 <= target_y < self_height:
                        target_px = (target_y * self_width) + target_x
                        
                        # I tried putting this if/else before px loop,
                        # surprisingly, there was not a noticable speed difference,
                        # and the code was harder to read. So, I put it back.
                        if use_tiny_fbuf:
                            # pack 4 bits into 8 bit ptr
                            target_idx = target_px // 2
                            dest_shift = ((target_px + 1) % 2) * 4
                            dest_mask = 0xf0 >> dest_shift
                            fbuf8[target_idx] = (fbuf8[target_idx] & dest_mask) | (color << dest_shift)
                        else:
                            # draw to 16 bits
                            target_idx = target_px
                            fbuf16[target_idx] = color
                    
                    px_idx += 1
                    
            x += width
            # early return for text off screen
            if x >= self_width:
                return


    def text(self, text, x, y, color, font=None):
        """
        Draw text to the framebuffer.
        
        Text is drawn with no background.
        If 'font' is None, uses the builtin framebuffer font.
        
        Args:
            text (str): text to write
            x (int): column to start drawing at
            y (int): row to start drawing at
            color (int): encoded color to use for text
            font (optional): bitmap font module to use
        """
        color = self._format_color(color)

        if font:
            self._set_show_min(y, y + font.HEIGHT)
            self._bitmap_text(font, text, x, y, color)
        else:
            self._set_show_min(y, y + 8)
            self.fbuf.text(text, x, y, color)


    def bitmap(self, bitmap, x, y, index=0, key=-1, palette=None):
        """
        Draw a bitmap on display at the specified column and row

        Args:
            bitmap (bitmap_module): The module containing the bitmap to draw
            x (int): column to start drawing at
            y (int): row to start drawing at
            index (int): Optional index of bitmap to draw from multiple bitmap
                module
            key (int): colors that match the key will be transparent.
        """
        if self.width <= x or self.height <= y:
            return
        
        if palette is None:
            palette = bitmap.PALETTE
        
        self._bitmap(bitmap, x, y, index, key, palette)


    @micropython.viper
    def _bitmap(self, bitmap, x:int, y:int, index:int, key:int, palette):
        
        width = int(bitmap.WIDTH)
        height = int(bitmap.HEIGHT)
        self_width = int(self.width)
        self_height = int(self.height)
        
        palette_len = int(len(palette))
        bpp = int(bitmap.BPP)
        bitmap_pixels = height * width
        starting_bit = bpp * bitmap_pixels * index  # if index > 0 else 0
        
        use_tiny_buf = bool(self.use_tiny_buf)
        
        self._set_show_min(y, y + height)
        
        
        # format color palette into a pointer
        palette_buf = bytearray(palette_len * 2)
        palette_ptr = ptr16(palette_buf)
        for i in range(palette_len):
            palette_ptr[i] = int(
                self._format_color(palette[i])
                )
        key = int(self._format_color(key))
        
        bitmap_ptr = ptr8(bitmap._bitmap)
        fbuf8 = ptr8(self.fbuf)
        fbuf16 = ptr16(self.fbuf)
        
        bitmask = 0xffff >> (16 - bpp)
        
        # iterate over pixels
        px_idx = 0
        while px_idx < bitmap_pixels:
            source_bit = (px_idx * bpp) + starting_bit
            source_idx = source_bit // 8 
            source_shift = 7 - (source_bit % 8)
            
            # bitmap value is an index in the color palette
            source = (bitmap_ptr[source_idx] >> source_shift) & bitmask
            clr = palette_ptr[source]
            
            target_x = x + px_idx % width
            target_y = y + px_idx // width
            
            # dont draw pixels off the screen (ptrs don't check your work!)
            if clr != key \
            and 0 <= target_x < self_width \
            and 0 <= target_y < self_height:
                
                # convert px coordinate to an index
                target_px = (target_y * self_width) + target_x
                
                if use_tiny_buf:
                    # writing 4-bit pixels
                    target_idx = target_px // 2
                    dest_shift = ((target_px + 1) % 2) * 4
                    dest_mask = 0xf0 >> dest_shift
                    fbuf8[target_idx] = (fbuf8[target_idx] & dest_mask) | (clr << dest_shift)
                else:
                    # TODO: TEST THIS! (has only been tested for tiny fbuf)
                    # writing 16-bit pixels
                    target_idx = target_px
                    fbuf16[target_idx] = clr
            
            px_idx += 1


    def polygon(self, coords, x, y, color, fill=False):
        """
        Draw a polygon from an array of coordinates

        Args:
            coords (array('h')): An array of x/y coordinates defining the shape
            x (int): column to start drawing at
            y (int): row to start drawing at
            color (int): Color of polygon
            fill (bool=False) : fill the polygon (or draw an outline)
        """
        # calculate approx height so min/max can be set
        h = max(coords)
        self._set_show_min(y, y + h)
        color = self._format_color(color)
        self.fbuf.poly(x, y, coords, color, fill)
