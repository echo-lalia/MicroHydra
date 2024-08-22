# lib.display

This is a module for drawing graphics to the display.

The module works using a `Display` class, which subclasses the relevant display driver *(currently only st7789.py, but can be extended to other drivers as well)*, and initializes it with the apropriate resolution, Pins, etc.

``` Py
from lib.display import Display

display = Display()
display.text("Hello, World!", x=5, y=10, color=display.palette[10])
display.show()
```
<br /><br /><br />


<br /><br />


# Display:

## Constructor:

> `display.Display(use_tiny_buf=False, **kwargs)`  
>> Initialize the display, and create the object for accessing it.
>> 
>> Args:
>> * `use_tiny_buf`:  
>>   If set to True, the driver will use a smaller 4bit (rather than 16bit) framebuffer with a limited palette.
>>   This uses roughly $\frac{width \times height}{2}$ bytes of RAM *(compared to $width \times height \times 2$ bytes normally)*.  
>>   This, however, does require extra processing when calling `display.show()`, so there is a speed trade-off when using it.
>> 
>> * `**kwargs`:  
>>   Any other keyword args given are passed along to the display driver.  
>> <br />

<br />

## Drawing Methods:
> `Display.vline(x:int, y:int, length:int, color:int)`
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

> `Display.hline(x:int, y:int, length:int, color:int)`
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

> `Display.pixel(x:int, y:int, color:int)`
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

> `Display.rect(x:int, y:int, w:int, h:int, color:int, fill:bool=False)`
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

> `Display.ellipse(x:int, y:int, xr:int, yr:int, color:int, fill:bool=False, m:int=0xf)`
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

> `Display.polygon(coords:array, x:int, y:int, color:int, fill:bool=False)`
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



> `Display.show()`
>> Write the framebuffer to the display  
>>  <br />