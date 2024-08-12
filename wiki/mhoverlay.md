MicroHydra includes a module called mhoverlay, which provides some simple, common tools for displaying various UI popups and overlays. 

To use the module, you must first import mhoverlay, and then create keyboard, config, and display objects, which you must pass to the mhoverlay.UI_Overlay object on creation. 

``` Python
import st7789py, keyboard, mhconfig, mhoverlay
from machine import Pin, 

tft = st7789py.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    rotation=1,
    color_order=st7789py.BGR
    )

kb = keyboard.KeyBoard()
config = Config()

# pass the  config, keyboard, and display objects to the overlay
overlay = UI_Overlay(config=config, keyboard=kb, display_py=tft)
```
UI_Overlay supports both st7789py, and st7789fbuf, but it requires you to specify which one you're using.

If you're using st7789py, you can use ```display_py=tft``` on initialization. However, for st7789fbuf, you can use ```display_fbuf=tft```.    
*Important note: If you are using st7789py, UI_Overlay will import font.vga1_8x16 to write to the screen.*

----

<br/>
<br/>
<br/>

#### Here's a quick overview on the methods provided by UI_Overlay:   

<br/>
<br/>

``` Python
UI_Overlay.text_entry(start_value='', title="Enter text:", blackout_bg=False)    
```
Creates a popup text box for the user to enter text. Blocks until user submits text with "enter" key. Returns entered text (str) or None if user backs out.    
*Params:*
- start_value(str): the value in the text field to start with
- title(str): the text to show above the text box
- blackout_bg(bool): whether or not to draw a large box behind textbox.

----
<br/>

``` Python
UI_Overlay.popup_options(options, title=None, shadow=True, extended_border=False)  
```
Creates a popup list of menu options, which the user can select with arrow keys + enter. Returns selection (str) or None if user hits escape.    
*Params:*
- options (list[str]): a list of menu options to choose from
- title (str): the text to show above the options
- shadow (bool): whether or not to draw a shadow behind the popup box
- extended_border (bool): whether or not to blackout a larger section behind the popup box (for, possibly, better readability)

----
<br/>

``` Python
UI_Overlay.popup(text)
```
Creates a popup message with the given text written in it. Blocks until user presses any key.    
*Params:*
- text (str): The text to write. This text will automatically be broken into lines to fit on the display.

----
<br/>

``` Python
UI_Overlay.error(text)
```
Similar to "popup"; creates a popup error message with the given text written in it. Blocks until user presses any key.    
*Params:*
- text (str): The text to write. This text will automatically be broken into lines to fit on the display.

----
<br/>

``` Python
UI_Overlay.draw_textbox(text, x, y, padding=8, shadow=True, extended_border=False):
```
Draw a textbox centered at the given position without blocking.    
*Params:*
- text (str): The text to write. 
- x (int): The x coordinate to center the textbox on
- y (int): The y coordinate to center the textbox on
- padding (int): The extra size added to the textbox, around the text
- shadow (bool): Whether or not to draw a shadow behind the text box
- extended_border (bool): Whether or not to blackout a larger region behind the popup box (to potentially improve readability)


----
<br/>

