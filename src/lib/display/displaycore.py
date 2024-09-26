"""The heart of MicroHydra graphics functionality."""


import framebuf
from .palette import Palette
from lib.hydra.utils import get_instance

# mh_if frozen:
# # frozen firmware must access the font as a module,
# # rather than a binary file.
# from font.utf8_8x8 import utf8
# mh_end_if



class DisplayCore:
    """The core graphical functionality for the Display module."""

    def __init__(
            self,
            width: int,
            height: int,
            *,
            rotation: int = 0,
            use_tiny_buf: bool = False,
            reserved_bytearray: bytearray|None = None,
            needs_swap: bool = True,
            **kwargs):  # noqa: ARG002
        """Create the DisplayCore.

        Args:
            width (int): display width
            height (int): display height
        Kwargs:
            rotation (int):
                How to rotate the framebuffer (Default 0)
            use_tiny_buf (bool):
                Whether or not to use a smaller, 4bit framebuffer (rather than 16 bit).
                If True, frame is stored in 4bits and converted line-by-line when `show` is called.
            reserved_bytearray (bytearray|None):
                A pre-allocated byte array to use for the framebuffer (rather than creating one on init).
            needs_swap (bool):
                Whether or not the RGB565 bytes must be swapped to show up correctly on the display.
            **kwargs (Any):
                Any other kwargs are captured and ignored.
                This is an effort to allow any future/additional versions of this module to be more compatible.
        """
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

        self.palette = get_instance(Palette)
        self.palette.use_tiny_buf = self.use_tiny_buf = use_tiny_buf

        # keep track of min/max y vals for writing to display
        # this speeds up drawing significantly.
        # only y value is currently used, because framebuffer is stored in horizontal lines,
        # making y slices much simpler than x slices.
        self._show_y_min = width if (rotation % 2 == 1) else height
        self._show_y_max = 0

        self.width = width
        self.height = height
        self.needs_swap = needs_swap




    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DisplayCore utils: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def reset_show_y(self) -> tuple[int, int]:
        """Return and reset y boundaries."""
        # clamp min and max
        y_min = max(self._show_y_min, 0)
        y_max = min(self._show_y_max, self.height)

        self._show_y_min = self.height
        self._show_y_max = 0

        return y_min, y_max


    @micropython.viper
    def _set_show_y(self, y0: int, y1: int):
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
    def _format_color(self, color: int) -> int:
        """Swap color bytes if needed, do nothing otherwise."""
        if (not self.use_tiny_buf) and self.needs_swap:
            color = ((color & 0xff) << 8) | (color >> 8)
        return color


    def blit_buffer(
            self,
            buffer: bytearray|framebuf.FrameBuffer,
            x: int,
            y: int,
            width: int,
            height: int,
            *,
            key: int = -1,
            palette: framebuf.FrameBuffer|None = None):
        """Copy buffer to display framebuf at the given location.

        Args:
            buffer (bytearray): Data to copy to display
            x (int): Top left corner x coordinate
            Y (int): Top left corner y coordinate
            width (int): Width
            height (int): Height
            key (int): color to be considered transparent
            palette (framebuf): the color pallete to use for the buffer
        """
        self._set_show_y(y, y + height)
        if not isinstance(buffer, framebuf.FrameBuffer):
            buffer = framebuf.FrameBuffer(
                buffer, width, height,
                framebuf.GS4_HMSB if self.use_tiny_buf else framebuf.RGB565,
                )

        self.fbuf.blit(buffer, x, y, key, palette)




    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ FrameBuffer Primitives: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def fill(self, color: int):
        """Fill the entire FrameBuffer with the specified color.

        Args:
            color (int): 565 encoded color
        """
        # whole display must show
        self._set_show_y(0, self.height)
        color = self._format_color(color)
        self.fbuf.fill(color)


    def pixel(self, x: int, y: int, color: int):
        """Draw a pixel at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            color (int): 565 encoded color
        """
        self._set_show_y(y, y)
        color = self._format_color(color)
        self.fbuf.pixel(x,y,color)


    def vline(self, x: int, y: int, length: int, color: int):
        """Draw vertical line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self._set_show_y(y, y + length)
        color = self._format_color(color)
        self.fbuf.vline(x, y, length, color)


    def hline(self, x: int, y: int, length: int, color: int):
        """Draw horizontal line at the given location and color.

        Args:
            x (int): x coordinate
            Y (int): y coordinate
            length (int): length of line
            color (int): 565 encoded color
        """
        self._set_show_y(y, y)
        color = self._format_color(color)
        self.fbuf.hline(x, y, length, color)


    def line(self, x0: int, y0: int, x1: int, y1: int, color: int):
        """
        Draw a single pixel wide line starting at x0, y0 and ending at x1, y1.

        Args:
            x0 (int): Start point x coordinate
            y0 (int): Start point y coordinate
            x1 (int): End point x coordinate
            y1 (int): End point y coordinate
            color (int): 565 encoded color
        """
        self._set_show_y(
            min(y0,y1),
            max(y0,y1),
        )
        color = self._format_color(color)
        self.fbuf.line(x0, y0, x1, y1, color)


    def rect(self, x: int, y: int, w: int, h: int, color: int, *, fill: bool = False):
        """Draw a rectangle at the given location, size and color.

        Args:
            x (int): Top left corner x coordinate
            y (int): Top left corner y coordinate
            width (int): Width in pixels
            height (int): Height in pixels
            color (int): 565 encoded color
        """
        self._set_show_y(y, y + h)
        color = self._format_color(color)
        self.fbuf.rect(x,y,w,h,color,fill)


    def fill_rect(self, x:int, y:int, width:int, height:int, color:int):
        """Draw a rectangle at the given location, size and filled with color.

        This is just a wrapper for the rect() method,
        and is provided for some compatibility with the original st7789py driver.
        """
        self.rect(x, y, width, height, color, fill=True)


    def ellipse(self, x:int, y:int, xr:int, yr:int, color:int, *, fill:bool=False, m:int=0xf):
        """Draw an ellipse at the given location, radius and color.

        Args:
            x (int): Center x coordinate
            y (int): Center y coordinate
            xr (int): x axis radius
            yr (int): y axis radius
            color (int): 565 encoded color
            fill (bool): fill in the ellipse. Default is False
        """
        self._set_show_y(y - yr, y + yr + 1)
        color = self._format_color(color)
        self.fbuf.ellipse(x,y,xr,yr,color,fill,m)


    def polygon(self, coords, x: int, y: int, color: int, *, fill: bool = False):
        """Draw a polygon from an array of coordinates.

        Args:
            coords (array('h')): An array of x/y coordinates defining the shape
            x (int): column to start drawing at
            y (int): row to start drawing at
            color (int): Color of polygon
            fill (bool=False) : fill the polygon (or draw an outline)
        """
        # calculate approx height so min/max can be set
        h = max(coords)
        self._set_show_y(y, y + h)
        color = self._format_color(color)
        self.fbuf.poly(x, y, coords, color, fill)


    def scroll(self, xstep: int, ystep: int):
        """Shift the contents of the FrameBuffer by the given vector.

        This is a wrapper for the framebuffer.scroll method.
        Args:
            xstep (int): Distance to move fbuf to the right
            ystep (int): Distance to move fbuf down
        """
        self._set_show_y(0, self.height)
        self.fbuf.scroll(xstep,ystep)




    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Text Drawing: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def text(self, text: str, x: int, y: int, color: int, font=None):
        """Draw text to the framebuffer.

        Text is drawn with no background.
        If 'font' is None, uses the built-in font.

        Args:
            text (str): text to write
            x (int): column to start drawing at
            y (int): row to start drawing at
            color (int): encoded color to use for text
            font (optional): bitmap font module to use
        """
        color = self._format_color(color)

        if font:
            self._set_show_y(y, y + font.HEIGHT)
            self._bitmap_text(font, text, x, y, color)
        else:
            self._set_show_y(y, y + 8)
            self._utf8_text(text, x, y, color)


    @micropython.viper
    def _bitmap_text(self, font, text, x:int, y:int, color:int):
        """Quickly draw a text with a bitmap font using viper.

        Designed to be envoked using the 'text' method.
        """
        width = int(font.WIDTH)
        height = int(font.HEIGHT)
        self_width = int(self.width)
        self_height = int(self.height)

        utf8_scale = height // 8

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
            else:
                # try drawing with utf8 instead
                x += int(self._utf8_putc(ch_idx, x, y, color, utf8_scale))

            # early return for text off screen
            if x >= self_width:
                return


    @micropython.viper
    def _utf8_putc(self, char:int, x:int, y:int, color:int, scale:int) -> int:
        """Render a single UTF8 character on the screen."""
        width = 4 if char < 128 else 8
        height = 8

        if not 0x0000 <= char <= 0xFFFF:
            return width * scale

        # set up viper variables
        use_tiny_fbuf = bool(self.use_tiny_buf)
        fbuf16 = ptr16(self.fbuf)
        fbuf8 = ptr8(self.fbuf)
        self_width = int(self.width)
        self_height = int(self.height)

        # calculate the offset in the binary data
        offset = char * 8

        # mh_if frozen:
        # # Read the font data directly from the memoryview
        # cur = ptr8(utf8)
        # mh_else:
        # seek to offset and read 8 bytes
        self.utf8_font.seek(offset)
        cur = ptr8(self.utf8_font.read(8))
        # mh_end_if

        # y axis is inverted - we start from bottom not top
        y += (height - 1) * scale - 1

        # iterate over every character pixel
        px_idx = 0
        max_px_idx = width * height
        while px_idx < max_px_idx:
            # which byte to fetch from the ptr8,
            # and how far to shift (to get 1 bit)
            ptr_idx = px_idx // 8
            shft_idx = px_idx % 8
            # mh_if frozen:
            # # if reading from memoryview, add offset now
            # ptr_idx += offset
            # mh_end_if

            # calculate x/y position from pixel index
            target_x = x + ((px_idx % width) * scale)
            target_y = y - ((px_idx // width) * scale)

            if (cur[ptr_idx] >> shft_idx) & 1 == 1:
                # iterate over x/y scale
                scale_idx = 0
                num_scale_pixels = scale * scale
                while scale_idx < num_scale_pixels:
                    xsize = scale_idx % scale
                    ysize = scale_idx // scale

                    target_px = ((target_y + ysize) * self_width) + target_x + xsize
                    if 0 <= (target_x + xsize) < self_width \
                    and 0 <= (target_y + ysize) < self_height:
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
                    scale_idx += 1
            px_idx += 1

        # return x offset for drawing next char
        return width * scale


    @micropython.viper
    def _utf8_text(self, text, x:int, y:int, color:int):
        """Draw text, including utf8 characters."""
        str_len = int(len(text))

        idx = 0
        while idx < str_len:
            char = text[idx]
            ch_ord = int(ord(char))
            if ch_ord >= 128:
                x += int(self._utf8_putc(ch_ord, x, y, color, 1))
            else:
                self.fbuf.text(char, x, y, color)
                x += 8
            idx += 1


    @staticmethod
    def get_total_width(text: str, *, width: int = 8) -> int:
        """Get the total width of a line (with UTF8 chars).

        Args:
            text (str): The text string to measure.
            width (int): Optional width of each (single-width) character.
        """
        return DisplayCore._get_total_width(text, len(bytes(text, "utf-8")), width)


    @staticmethod
    @micropython.viper
    def _get_total_width(text_ptr: ptr8, text_len: int, width: int) -> int:
        """Fast viper component of get_total_width.

        Scans over raw string bytes to count number of single-byte or multi-byte characters.
        Saves a lot of time by not fully decoding any code-points,
        and by skipping function call overhead from `ord`.
        """
        total_width = 0
        idx = 0
        while idx < text_len:
            # count leading 1's to determine byte type
            # 0 = Single Byte, 1 = continuation byte
            # 2-4 = Start byte (stop testing after 2)
            leading_bytes = 0
            byte_shift = 7
            while leading_bytes < 2:
                if text_ptr[idx] >> byte_shift & 1:
                    leading_bytes += 1
                    byte_shift -= 1
                else:
                    break

            # single byte chars have width 8, others have width 16
            # ignore continuation bytes.
            if leading_bytes == 0:  # single byte char
                total_width += 1
            elif leading_bytes > 1:  # multi byte char
                total_width += 2

            idx += 1

        return total_width * width




    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Bitmap Drawing: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def bitmap(
            self,
            bitmap,
            x: int,
            y: int,
            *,
            index: int = 0,
            key: int = -1,
            palette: list[int]|None = None):
        """Draw a bitmap on display at the specified column and row.

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

        self._set_show_y(y, y + height)

        # format color palette into a pointer
        palette_buf = bytearray(palette_len * 2)
        palette_ptr = ptr16(palette_buf)
        for i in range(palette_len):
            palette_ptr[i] = int(
                self._format_color(palette[i])
                )
        key = int(self._format_color(key))

        bitmap_ptr = ptr8(bitmap.BITMAP)
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
                    # writing 16-bit pixels
                    target_idx = target_px
                    fbuf16[target_idx] = clr

            px_idx += 1
