# lib.display

A module for drawing graphics to the display.

The module works using a `Display` class, which subclasses the relevant display driver *(currently only st7789.py, but can be extended to other drivers as well)*, and initializes it with the apropriate settings for the device.  
The display driver class itself also subclasses the `DisplayCore` module, which is where the main graphics logic for MicroHydra resides.

``` Py
from lib.display import Display

display = Display()
# Draw text to the framebuffer, then write the frambuffer to the display:
display.text("Hello, World!", x=5, y=10, color=display.palette[10])
display.show()
```
<br /><br /><br />




# Display:

## Constructor:

> ``` py
> display.Display(
>    use_tiny_buf: bool = False,
>    reserved_bytearray: bytearray|None = None,
>    **kwargs,
> )
> ```
>> Initialize the display, and create the object for accessing it.
>> 
>> Args:
>> * `use_tiny_buf`:  
>>   If set to True, the driver will use a smaller 4bit (rather than 16bit) framebuffer with a limited palette.
>>   This uses roughly $\frac{width \times height}{2}$ bytes of RAM *(compared to $width \times height \times 2$ bytes normally)*.  
>>   This, however, does require extra processing when calling `display.show()`, so there is a speed trade-off when using it.
>> * `reserved_bytearray`:  
>>   A pre-allocated bytearray to use for the framebuffer (rather than creating one on init).
>> * `**kwargs`:  
>>   Any other keyword args given are passed along to the display driver, and then to `DisplayCore`.  
>> <br />

<br />

## Primitive Drawing Methods:

> ```Py
> Display.pixel(x:int, y:int, color:int)
> ```
>> Set the color of one pixel.
>> 
>> Args:  
>> * `x`:  
>>   horizontal position of the pixel  
>> * `Y`:  
>>   Vertical position of the pixel
>> * `color`:  
>>   565 encoded color  
>>  <br />

> ```Py
> Display.vline(x:int, y:int, length:int, color:int)
> ```
>> Draw a vertical line.
>> 
>> Args:  
>> * `x`:  
>>   horizontal position of to start the line at  
>> * `Y`:  
>>   Vertical position to start the line at
>> * `length`:  
>>   Length of line to draw  
>> * `color`:  
>>   565 encoded color  
>>  <br />

> ```Py
> Display.hline(x:int, y:int, length:int, color:int)
> ```
>> Draw a horizontal line.
>> 
>> Args:  
>> * `x`:  
>>   horizontal position of to start the line at  
>> * `Y`:  
>>   Vertical position to start the line at
>> * `length`:  
>>   Length of line to draw  
>> * `color`:  
>>   565 encoded color  
>>  <br />

> ```Py
> Display.line(x0:int, y0:int, x1:int, y1:int, color:int)
> ```
>> Draw a single pixel wide line starting at x0, y0 and ending at x1, y1.
>> 
>> Args:  
>> * `x0`: Start point x coordinate  
>> * `y0`: Start point y coordinate  
>> * `x1`: End point x coordinate  
>> * `y1`: End point y coordinate  
>> * `color`: 565 encoded color  
>>  <br />

> ```Py
> Display.rect(x:int, y:int, w:int, h:int, color:int, *, fill:bool=False)
> ```
>> Draw a rectangle starting at a given point
>> 
>> Args:  
>> * `x`:  
>>   X position for the top left corner of the rectangle   
>> * `Y`:  
>>   Y position for the top left corner of the rectangle   
>> * `w`:  
>>   Width of the rectangle
>> * `h`:  
>>   Height of the rectangle   
>> * `color`:  
>>   565 encoded color  
>> * `fill`:  
>>   Whether to fill in the rectangle (or just draw the outline)  
>>  <br />

> ```Py
> Display.ellipse(x:int, y:int, xr:int, yr:int, color:int, *, fill:bool=False, m:int=0xf)
> ```
>> Draw an ellipse centered on the given point.
>> 
>> Args:  
>> * `x`:  
>>   Horizontal center of the ellipse   
>> * `Y`:  
>>   Vertical center of the ellipse   
>> * `xr`:  
>>   The radius on the X axis
>> * `yr`:  
>>   The radius on the Y axis   
>> * `color`:  
>>   565 encoded color  
>> * `fill`:  
>>   Whether to fill in the ellipse (or just draw the outline)
>> * `m`:  
>>   Enables drawing only specific quadrants of the ellipse, by selecting quadrants using 4 bits.  
>>   See the [FrameBuffer](https://docs.micropython.org/en/latest/library/framebuf.html#framebuf.FrameBuffer.ellipse) documentation for a full explanation  
>>  <br />

> ```Py
> Display.polygon(coords:array, x:int, y:int, color:int, *, fill:bool=False)
> ```
>> Draw an arbitrary closed polygon, starting from the given location.
>> 
>> Args:  
>> * `coords`:  
>>   An array of integers *(e.g. `array('h', [x0, y0, x1, y1... )`)* specifying the coordinates for each point of the polygon  
>> * `x`:  
>>   Horizontal start position of the polygon  
>> * `Y`:  
>>   Vertical start position of the polygon  
>> * `fill`:  
>>   Whether or not to fill in the polygon (or just draw the outline)  
>>  <br />


<br />

## Text Drawing Methods:

> ```Py
> Display.text(
>     text: str,
>     x: int,
>     y: int,
>     color: int,
>     font = None,
> )
> ```
>> Draw text to the framebuffer.
>>
>> Text is drawn with no background.
>>
>> Args: 
>> * `text`: A string of text to draw
>> * `x`: The x coordinate to start drawing at
>> * `y`: The y coordinate to start drawing at
>> * `color`: An RGB565 color
>> * `font`:  
>>     An optional bitmap font module to use for drawing.  
>>     If `font` is `None`, uses the built-in FrameBuffer font.  
>>     In both cases, uses MH's built-in UTF8 font for chars not in the other font.  
>>  <br />

> ```Py
> Display.get_total_width(text: str, *, font=None) -> int
> ```
>> Get the total pixel width of a line (with UTF8 chars).
>> 
>> Args:
>> * `text`: A string of text, to calculate the width of  
>> * `font`: The font you are using to draw this text  
>>  <br />

<br />

## Other Methods:

> ```Py
> Display.bitmap(
>     self,
>     bitmap,
>     x: int,
>     y: int,
>     *,
>     index: int = 0,
>     key: int = -1,
>     palette: list[int]|None = None):
> ```
>> Draw a bitmap on display at the specified column and row.
>>
>> Uses converted bitmaps, like the kind output by the `image_converter` or `sprites_converter` scripts, [here](https://github.com/russhughes/st7789py_mpy/tree/master/utils).
>> 
>> Args:  
>> * `bitmap`: The module containing the converted bitmap to draw  
>> * `x`: Column to start drawing at  
>> * `y`: Row to start drawing at  
>> * `index`: Optional index of bitmap to draw (For modules with multiple bitmaps)  
>> * `key`: Optional color to treat as transparent when drawing bitmap  
>> * `palette`: Optional palette to use for drawing the bitmap. Defaults to `bitmap.PALETTE`.  
>>  <br />

> ```Py
> Display.blit_buffer(
>     buffer: bytearray|framebuf.FrameBuffer,
>     x: int,
>     y: int,
>     width: int,
>     height: int,
>     *,
>     key: int = -1,
>     palette: framebuf.FrameBuffer|None = None,
> )
> ```
>> Copy buffer to display framebuf at the given location.
>> 
>> Args:  
>> * `buffer`: Data to copy to display.   
>> * `x`:  Top left corner x coordinate
>> * `y`:  Top left corner y coordinate
>> * `width`:  Height of buffer to draw
>> * `height`: Height of buffer to draw 
>> * `key`: Optional color to treat as transparent when drawing image
>> * `palette`: A FrameBuffer color palette (To be passed to the `FrameBuffer.blit` method)  
>>  <br />

> ```Py
> Display.scroll(xstep:int, ystep:int)
> ```
>> Shift the contents of the FrameBuffer by the given vector.
>> 
>> This is a wrapper for the `FrameBuffer.scroll` method.
>> Args:  
>> * `xstep`: Distance to move fbuf to the right  
>> * `ystep`: Distance to move fbuf down  
>>  <br />

> ```Py
> Display.show()
> ```
>> Write the current framebuffer to the display  
>>  <br />

<br /><br />

## Overlay Callbacks:
The Display also has an attribute for storing overlay drawing functions.

`Display.overlay_callbacks` is a list of callbacks, to be called every time `Display.show()` is called (before writing the framebuffer).  
The callbacks should accept the the `Display` object as a single positional argument.

This is how the `userinput` module is able to draw 'locked' modifier keys over top of the other graphics on screen.  
One major limitation of this, is that because the graphics in the callbacks work identically to the normal graphics, the overlaid graphics will persist across frames, unless the app is also redrawing that section of the display.
