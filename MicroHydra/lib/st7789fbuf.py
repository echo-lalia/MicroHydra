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
Specifically, it has been made for MicroHydra on the Cardputer

This module will use a lot more ram than the original, but it should be much faster too.

This driver supports:

- 320x240, 240x240, 135x240 and 128x128 pixel displays
- Display rotation
- RGB and BGR color orders
- Hardware based scrolling
- Drawing text using 8 and 16 bit wide bitmap fonts with heights that are
  multiples of 8.  Included are 12 bitmap fonts derived from classic pc
  BIOS text mode fonts.
- Drawing text using converted TrueType fonts.
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

from math import sin, cos, floor, pi, sqrt, pow
import framebuf, struct, array

#
# This allows sphinx to build the docs
#

try:
    from time import sleep_ms
except ImportError:
    sleep_ms = lambda ms: None
    uint = int
    const = lambda x: x

    class micropython:
        @staticmethod
        def viper(func):
            return func

        @staticmethod
        def native(func):
            return func


#
# If you don't need to build the docs, you can remove all of the lines between
# here and the comment above except for the "from time import sleep_ms" line.
#



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

RGB = 0x00
BGR = 0x08

# Color modes
_COLOR_MODE_65K = const(0x50)
_COLOR_MODE_262K = const(0x60)
_COLOR_MODE_12BIT = const(0x03)
_COLOR_MODE_16BIT = const(0x05)
_COLOR_MODE_18BIT = const(0x06)
_COLOR_MODE_16M = const(0x07)

# Color definitions
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

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

_DISPLAY_240x320 = (
    (0x00, 240, 320, 0, 0, False),
    (0x60, 320, 240, 0, 0, False),
    (0xc0, 240, 320, 0, 0, False),
    (0xa0, 320, 240, 0, 0, False))

_DISPLAY_240x240 = (
    (0x00, 240, 240,  0,  0, False),
    (0x60, 240, 240,  0,  0, False),
    (0xc0, 240, 240,  0, 80, False),
    (0xa0, 240, 240, 80,  0, False))

_DISPLAY_135x240 = (
    (0x00, 135, 240, 52, 40, False),
    (0x60, 240, 135, 40, 53, False),
    (0xc0, 135, 240, 53, 40, False),
    (0xa0, 240, 135, 40, 52, False))

_DISPLAY_128x128 = (
    (0x00, 128, 128, 2, 1, False),
    (0x60, 128, 128, 1, 2, False),
    (0xc0, 128, 128, 2, 1, False),
    (0xa0, 128, 128, 1, 2, False))

# index values into rotation table
_WIDTH = const(0)
_HEIGHT = const(1)
_XSTART = const(2)
_YSTART = const(3)
_NEEDS_SWAP = const(4)

# Supported displays (physical width, physical height, rotation table)
_SUPPORTED_DISPLAYS = (
    (240, 320, _DISPLAY_240x320),
    (240, 240, _DISPLAY_240x240),
    (135, 240, _DISPLAY_135x240),
    (128, 128, _DISPLAY_128x128))

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
    ( b'\x29', b'\x00', 120)                # Turn on the display
)

# fmt: on


def color565(red, green=0, blue=0):
    """
    Convert red, green and blue values (0-255) into a 16-bit 565 encoding.
    """
    if isinstance(red, (tuple, list)):
        red, green, blue = red[:3]
    return (red & 0xF8) << 8 | (green & 0xFC) << 3 | blue >> 3

def swap_bytes(color):
    """
    this just flips the left and right byte in the 16 bit color.
    """
    return ((color & 255) << 8) + (color >> 8) 

def scale_poly(points, scale=1.2):
    """
    Resize all the points in the array. Returns None.
    """
    for idx, point in enumerate(points):
        points[idx] = floor(point * scale)

def rotate_points(points, angle=0, center_x=0, center_y=0):
    """
    Rotate all the points in the array, return resulting array.
    """
    if angle:
        cos_a = cos(angle)
        sin_a = sin(angle)
        rotated = array.array('h')
        for i in range(0,len(points),2):
            rotated.append(
                center_x + floor((points[i] - center_x) * cos_a - (points[i+1] - center_y) * sin_a)
            )
            rotated.append(
                center_y + floor((points[i] - center_x) * sin_a + (points[i+1] - center_y) * cos_a)    
            )
        return rotated
    else:
        return points

def warp_points(points, tilt_center=0.5, ease=True, focus_center_x=True, smallest=None, largest=None):
    """
    Skew points on the y axis. Can create a faux 3d looking effect, or a kinda jelly-like effect.
    """
    if tilt_center == 0.5 and not ease:
        return points
    
    if smallest == None:
        smallest = min(points)
    if largest == None:
        largest = max(points)

    midpoint = (smallest + largest) / 2
    #shift numbers so that the smallest point = 0
    adj_largest = largest - smallest
    adj_midpoint = adj_largest / 2
    new_adj_midpoint = adj_largest * tilt_center
    
    #shift largest down, (along with newmidpoint), so that newmidpoint = 0
    #this is done so that we can interpolate between 0 and this number, then re-add the midpoint
    temp_largest = adj_largest - new_adj_midpoint
    
    #iterate over each point
    # if point is less than midpoint, interpolate point between 0 and new midpoint
    # if point is greater than midpoint, interpolate between new midpoint and largest
    # then add the smallest value back to the result, to shift the result into the original range
    #for index, point in enumerate(points):
    for index in range(1,len(points),2):
        point=points[index]
        
        if focus_center_x:
            #if focus_center_x, then apply the effect more strongly to points nearer to the center x
            adj_x_val = points[index-1] - smallest
            x_center_factor = abs(adj_x_val - adj_midpoint ) / adj_midpoint
            x_center_factor = ease_in_out_circ(x_center_factor)
        
        if point < midpoint:
            #find fac between 0 and adj_midpoint,
            #then interpolate between 0 and new midpoint
            adj_point = point - smallest
            factor = adj_point / adj_midpoint
            
            #fancy easing function to round out the shape more
            factor = ease_in_out_sine(factor)
            
            if focus_center_x:
                points[index] = floor(
                    mix(
                        (new_adj_midpoint * factor) + smallest, points[index], x_center_factor
                        ))
            else:
                points[index] = floor((new_adj_midpoint * factor) + smallest)


        else: # point >= midpoint:
            #find fac between adj_midpoint and adj_largest,
            #then interpolate between new midpoint and largest
            adj_point = point - smallest
            factor = (adj_point - adj_midpoint) / (adj_largest - adj_midpoint)
            
            #fancy easing function to round out the shape more
            factor = ease_in_out_sine(factor)
            
            if focus_center_x:
                points[index] = floor(
                    mix(
                        (temp_largest * factor) + new_adj_midpoint + smallest,points[index],x_center_factor
                        )
                    )
            else:
                points[index] = floor((temp_largest * factor) + new_adj_midpoint + smallest)       
            
    return points

def mix(val2, val1, fac=0.5):
    """Mix two values to the weight of fac"""
    output = (val1 * fac) + (val2 * (1.0 - fac))
    return output


def ease_in_out_sine(x):
    return -(cos(pi * x) - 1) / 2

def ease_in_out_circ(x):
    if x < 0.5:
        return (1 - sqrt(1 - pow(2 * x, 2))) / 2
    else:
        return (sqrt(1 - pow(-2 * x + 2, 2)) + 1) / 2

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
        
        #init the fbuf
        if rotation == 1 or rotation == 3:
            self.fbuf = framebuf.FrameBuffer(bytearray(height*width*2), height, width, framebuf.RGB565)
        else:
            self.fbuf = framebuf.FrameBuffer(bytearray(height*width*2), width, height, framebuf.RGB565)
        
        self.physical_width = self.width = width
        self.physical_height = self.height = height
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
        self.needs_swap = True
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
            sleep_ms(delay)

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
        if value:
            self._write(_ST7789_SLPIN)
        else:
            self._write(_ST7789_SLPOUT)

    def inversion_mode(self, value):
        """
        Enable or disable display inversion mode.

        Args:
            value (bool): if True enable inversion mode. if False disable
            inversion mode
        """
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
        if self.needs_swap:
            color = swap_bytes(color)
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
        if self.needs_swap:
            color = swap_bytes(color)
        self.fbuf.hline(x, y, length, color)

    def pixel(self, x, y, color):
        """
        Draw a pixel at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            color (int): 565 encoded color
        """
        if self.needs_swap:
            color = swap_bytes(color)
        self.fbuf.pixel(x,y,color)
        
        
    def show(self):
        """
        Write the current framebuf to the display
        """
        self._set_window(0, 0, self.width - 1, self.height - 1)
        self._write(None, self.fbuf)
        
        
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
        self.fbuf.blit(framebuf.FrameBuffer(buffer,width, height, framebuf.RGB565), x,y,key,palette)
        
    def blit_framebuf(self, fbuf, x, y, key=-1, palette=None):
        """
        Copy FrameBuffer to internal FrameBuffer at the given location.
        
        This is an alternate version of blit_buffer,
        which does not create a new framebuffer on use.
        This can be useful for reusing a framebuffer multiple times.

        Args:
            fbuf (bytes): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
            buffer_format (framebuf format): the color format to use for the blit function. 
            key (int): color to be considered transparent
            palette (framebuf): the color pallete to use for the buffer
        """
        self.fbuf.blit(fbuf, x,y,key,palette)

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
        if self.needs_swap:
            color = swap_bytes(color)
        self.fbuf.rect(x,y,w,h,color,fill)
        
    def ellipse(self, x, y, xr, yr, color, fill=False):
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
        if self.needs_swap:
            color = swap_bytes(color)
        self.fbuf.ellipse(x,y,xr,yr,color,fill)

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
        self.rect(x, y, width, height, color, fill=True)

    def fill(self, color):
        """
        Fill the entire FrameBuffer with the specified color.

        Args:
            color (int): 565 encoded color
        """
        if self.needs_swap:
            color = swap_bytes(color)
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
        self.fbuf.line(x0, y0, x1, y1, color)

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
        self._write(_ST7789_VSCRDEF, struct.pack(">HHH", tfa, vsa, bfa))

    def vscsad(self, vssa):
        """
        Set Vertical Scroll Start Address of RAM.

        Defines which line in the Frame Memory will be written as the first
        line after the last line of the Top Fixed Area on the display

        Example:

            for line in range(40, 280, 1):
                tft.vscsad(line)
                utime.sleep(0.01)

        Args:
            vssa (int): Vertical Scrolling Start Address

        """
        self._write(_ST7789_VSCSAD, struct.pack(">H", vssa))

    def scroll(self,xstep,ystep):
        """
        Shift the contents of the FrameBuffer by the given vector.
        This may leave a footprint of the previous colors in the FrameBuffer.

        Unlike vscsad which uses the hardware for scrolling,
        this method scrolls the framebuffer itself.
        This is a wrapper for the framebuffer.scroll method:
        """
        self.fbuf.scroll(xstep,ystep)

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

    def _text8(self, font, text, x0, y0, fg_color=WHITE):
        """
        Internal method to write characters with width of 8 and
        heights of 8 or 16.

        Args:
            font (module): font module to use
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
        """
        if fg_color == 0:
            bg_color = 1
        else:
            bg_color = 0
            
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
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 8, 8,key=bg_color)

                x0 += 8

    def _text16(self, font, text, x0, y0, fg_color=WHITE):
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
        if fg_color == 0:
            bg_color = 1
        else:
            bg_color = 0
        for char in text:
            ch = ord(char)
            if (
                font.FIRST <= ch < font.LAST
                and x0 + font.WIDTH <= self.width
                and y0 + font.HEIGHT <= self.height
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
                    buffer = self._pack16(font.FONT, idx, fg_color, bg_color)
                    self.blit_buffer(buffer, x0, y0 + 8 * line, 16, 8,key=bg_color)
            x0 += 16

    def text(self, text, x, y, color=WHITE):
        """
        Quickly draw text to the display using the FrameBuffer text method.
        
        This uses the font built into the FrameBuffer class, and so custom fonts are not supported.
        
        Args:
            text (str): text to write
            x (int): column to start drawing at
            y (int): row to start drawing at
            color (int): 565 encoded color to use for text
        """
        if self.needs_swap:
            color = swap_bytes(color)
        self.fbuf.text(text, x, y, color)

    def bitmap_text(self, font, text, x0, y0, color=WHITE):
        """
        Draw text on display in specified font and colors. 8 and 16 bit wide
        fonts are supported.

        Args:
            font (module): font module to use.
            text (str): text to write
            x0 (int): column to start drawing at
            y0 (int): row to start drawing at
            color (int): 565 encoded color to use for characters
        """
        if self.needs_swap:
            color=swap_bytes(color)

        if font.WIDTH == 8:
            self._text8(font, text, x0, y0, color)
        else:
            self._text16(font, text, x0, y0, color)

    def bitmap(self, bitmap, x, y, index=0, key=-1):
        """
        Draw a bitmap on display at the specified column and row

        Args:
            bitmap (bitmap_module): The module containing the bitmap to draw
            x (int): column to start drawing at
            y (int): row to start drawing at
            index (int): Optional index of bitmap to draw from multiple bitmap
                module
            key (int): colors that match they key will be transparent.
        """
        width = bitmap.WIDTH
        height = bitmap.HEIGHT
        to_col = x + width - 1
        to_row = y + height - 1
        if self.width <= to_col or self.height <= to_row:
            return

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = bitmap.BPP
        bs_bit = bpp * bitmap_size * index  # if index > 0 else 0
        palette = bitmap.PALETTE
        
        #swap colors if needed:
        if self.needs_swap:
            for i in range(0,len(palette)):
                palette[i] = swap_bytes(palette[i])
        
        buffer = bytearray(buffer_len)

        for i in range(0, buffer_len, 2):
            color_index = 0
            for _ in range(bpp):
                color_index = (color_index << 1) | (
                    (bitmap.BITMAP[bs_bit >> 3] >> (7 - (bs_bit & 7))) & 1
                )
                bs_bit += 1

            color = palette[color_index]

            buffer[i] = color & 0xFF
            buffer[i + 1] = color >> 8
        
        self.blit_buffer(buffer,x,y,width,height,key=key)
        #self._set_window(x, y, to_col, to_row)
        #self._write(None, buffer)

    def bitmap_icons(self, bitmap_module, bitmap, color, x, y, invert_colors=False):
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
        if self.width <= to_col or self.height <= to_row:
            return

        bitmap_size = height * width
        buffer_len = bitmap_size * 2
        bpp = bitmap_module.BPP
        bs_bit = 0
        needs_swap = self.needs_swap
        buffer = bytearray(buffer_len)
        
        if self.needs_swap:
            color = swap_bytes(color)
            
        #prevent bg color from being invisible
        if color == 0:
            palette = (65535, color)
        else:
            palette = (0, color)
        
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

        
        self.blit_buffer(buffer,x,y,width,height,key=palette[0])
                
            
#     def write(self, font, string, x, y, fg=WHITE, bg=None):
#         #key out bg when unspecified
#         key=-1
#         if bg==None:
#             if fg == 0:
#                 bg = 65535
#                 key = 65535
#             else:
#                 bg = 0
#                 key = 0
#         buffer_len = font.HEIGHT * font.MAX_WIDTH * 2
#         buffer = bytearray(buffer_len)
#         fg_hi = fg >> 8
#         fg_lo = fg & 0xFF
#         bg_hi = bg >> 8
#         bg_lo = bg & 0xFF
#         for character in string:
#             try:
#                 char_index = font.MAP.index(character)
#                 offset = char_index * font.OFFSET_WIDTH
#                 bs_bit = font.OFFSETS[offset]
#                 
#                 if font.OFFSET_WIDTH > 2:
#                     bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 2]
#                 elif font.OFFSET_WIDTH > 1:
#                     bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 1]
#                 char_width = font.WIDTHS[char_index]
#                 buffer_needed = char_width * font.HEIGHT * 2
#                 for i in range(0, buffer_needed, 2):
#                     if font.BITMAPS[bs_bit // 8] & 1 << (7 - (bs_bit % 8)) > 0:
#                         buffer[i] = fg_hi
#                         buffer[i + 1] = fg_lo
#                     else:
#                         buffer[i] = bg_hi
#                         buffer[i + 1] = bg_lo
#                     bs_bit += 1
#                 self.blit_buffer(buffer,x,y,char_width,font.HEIGHT,key=key)
#                 x += char_width
#             except ValueError:
#                 pass

    def write(self, font, string, x, y, fg=WHITE):
        """
        Write a string using a converted true-type font on the display starting
        at the specified column and row

        Args:
            font (font): The module containing the converted true-type font
            s (string): The string to write
            x (int): column to start writing
            y (int): row to start writing
            fg (int): foreground color, optional, defaults to WHITE
            bg (int): background color, optional, defaults to None
        """
        if self.needs_swap:
            fg = swap_bytes(fg)
            
        for character in string:
            try:
                char_index = font.MAP.index(character)
                offset = char_index * font.OFFSET_WIDTH
                bs_bit = font.OFFSETS[offset]
                
                if font.OFFSET_WIDTH > 2:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 2]
                elif font.OFFSET_WIDTH > 1:
                    bs_bit = (bs_bit << 8) + font.OFFSETS[offset + 1]
                
                char_width = font.WIDTHS[char_index]
                buffer_needed = char_width * font.HEIGHT
                
                for i in range(0, buffer_needed):
                    px_x = x + ((i) % char_width)
                    px_y = y + ((i) // char_width)
                    if font.BITMAPS[bs_bit // 8] & 1 << (7 - (bs_bit % 8)) > 0:
                        self.fbuf.pixel(px_x,px_y,fg)
                    
                    bs_bit += 1

                x += char_width

            except ValueError:
                print("ValueError in write; probably because a char used doesn't exists in the font")
                pass

    def write_width(self, font, string):
        """
        Returns the width in pixels of the string if it was written with the
        specified font

        Args:
            font (font): The module containing the converted true-type font
            string (string): The string to measure

        Returns:
            int: The width of the string in pixels

        """
        width = 0
        for character in string:
            try:
                char_index = font.MAP.index(character)
                width += font.WIDTHS[char_index]
            except ValueError:
                pass

        return width
    
    def simple_poly(self,points,x,y,color,fill=False):
        """
        Draw a polygon on the display.

        Args:
            points (array('h')): Array of points to draw.
            x (int): X-coordinate of the polygon's position.
            y (int): Y-coordinate of the polygon's position.
            color (int): 565 encoded color.
        """
        if self.needs_swap:
            color = swap_bytes(color)
        self.fbuf.poly(x,y,points,color,fill)
    
    
    
    def polygon(self, points, x, y, color, angle=0, center_x=None, center_y=None, scale=1, warp=None, fill=False):
        """
        Draw a polygon on the display.

        Args:
            points (array('h')): Array of points to draw.
            x (int): X-coordinate of the polygon's position.
            y (int): Y-coordinate of the polygon's position.
            color (int): 565 encoded color.
            angle (float): Rotation angle in radians (default: 0).
            center_x (int): X-coordinate of the rotation center (default: 0).
            center_y (int): Y-coordinate of the rotation center (default: 0).
        """
        
        #simple poly wrapper
        if angle == 0 and scale == 1 and warp == None:
            if self.needs_swap:
                color = swap_bytes(color)
            self.fbuf.poly(x,y,points,color,fill)
        
        #complex polygon
        else:
            if self.needs_swap:
                color = swap_bytes(color)
            #clone array so we don't modify original
            points = array.array('h',points)
            
            #scale
            if scale != 1:
                scale_poly(points,scale)
            
            if center_x == None:
                center_x = max(points) // 2
            if center_y == None:
                center_y = max(points) // 2
            
            #rotate
            if angle != 0:
                points = rotate_points(points, angle, center_x, center_y)
                
            if warp != None:
                warp_points(points, warp)
            
            self.fbuf.poly(x,y,points,color,fill)

