There are two main display drivers that come with MicroHydra: st7789py, and st7789fbuf.   
MH apps are free to use any other driver that they'd like, ,and there may be more performance to be gained by doing so. However, one of these built-in drivers should be good enough for most uses. 

<br /><br /><br />


### st7789fbuf
[st7789fbuf.py](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/main/MicroHydra/lib/st7789fbuf.py) is a fork of st7789py.py *(more on that below)*, which was made to speed up graphics, and make updates to the display looks smoother. 

This driver works by utilizing the inbuilt MicroPython FrameBuffer class. The framebuffer library is very fast, and this driver is capable of much faster, smoother graphics than the other version. However, it also uses more memory, because a framebuffer for the entire display must be allocated to use it. 

This module is working well as far as I can tell, but it's still a work-in-progress, and likely has some issues that will pop up. Documentation for this module is also incomplete at the moment, however, for the most part it works the same as st7789py. Feel free to browse through the .py file itself and take a look at what the driver can do.

Here's a quick example of it's usage:

``` Python
from lib import st7789fbuf
from machine import Pin, SPI
from font import vga2_16x32 as font

tft = st7789fbuf.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
    )

# blackout display
tft.fill(0)

# text method now uses built-in font. It's very fast but also small. 
tft.text('Hello world!', 72,40,65535)

# bitmap fonts can still  be used like this:
tft.bitmap_text(font, "Hello WORLD!", 24,80, 65535)

# show method writes the framebuffer to the display.
tft.show()
```



***

<br /><br /><br />


### st7789py
[st7789py.py](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/main/MicroHydra/lib/st7789py.py) comes from [here](https://github.com/russhughes/st7789py_mpy), and is the main LCD driver used by the launcher. The linked repository also has examples and utilities for converting images and fonts into python files, which can be read by the driver. 

<br />

The st7789py driver is easy to use and contains some useful tools such as hardware scrolling. This driver does not use a framebuffer, and instead writes all changes directly to the display. It is fairly slow, but it uses relatively low memory, and has some handy tricks that can be used for smooth looking graphics. This is the driver used by the main launcher. 

<br />

In the context of MicroHydra on the Cardputer, you can use the driver like this:   
``` Python
from lib import st7789py as st7789
from machine import Pin, SPI
```   

``` Python
#define static vars for our display settings
display_width = const(240)
display_height = const(135)

#init driver for the graphics
spi = SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None)

tft = st7789.ST7789(
spi,
display_height,
display_width,
reset=Pin(33, Pin.OUT),
cs=Pin(37, Pin.OUT),
dc=Pin(34, Pin.OUT),
backlight=Pin(38, Pin.OUT),
rotation=1,
color_order=st7789.BGR
)

#init display by blacking out the screen
tft.fill(st7789.color565(0,0,0))
```

And there are a bunch more methods in the ST7789 class that you can use for drawing text, images polygons, and for scrolling the display.   
Check out the st7789py.py for more details on all of its features.

