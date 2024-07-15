from lib import st7789fbuf, mhconfig, keyboard
import machine, time
"""
MicroHydra REPL Interface
Version: 1.0

Support for Micropython REPL (Read-Eval-Print Loop).
Have fun!

TODO:
KFC V me 50
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
tft = st7789fbuf.ST7789(
    machine.SPI(
        1,baudrate=40000000,sck=machine.Pin(36),mosi=machine.Pin(35),miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
    )

# object for accessing microhydra config (Delete if unneeded)
config = mhconfig.Config()

# object for reading keypresses
kb = keyboard.KeyBoard()

#screen buffer
scr_buf = [""]*13

#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

def scr_feed(str):
    for i in range(1,12):
        scr_buf[i-1] = scr_buf[i]
    scr_buf[11] = str
    
def scr_show():
    # clear framebuffer 
    tft.fill(config['bg_color'])
    
    # write current text to framebuffer
    for i in range(12):
        tft.text(
            text=scr_buf[i],
            # center text on x axis:
            x=0, 
            y=10*i,
            color=config['ui_color']
            )
    # write framebuffer to display
    tft.show()

#Used for Peeking Stdout
import sys

class OutputBuffer:
    def __init__(self):
        self.content = []

    def write(self, string):
        self.content.append(string)

    def getvalue(self):
        return ''.join(self.content)
    
    def clear(self):
        self.content = []

# Create an output buffer instance
output_buffer = OutputBuffer()

# Custom print function that writes to the buffer
def custom_print(*args, **kwargs):
    output_buffer.write(' '.join(map(str, args)) + kwargs.get('end', '\n'))

# Replace the built-in print function with the custom one
print = custom_print

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """
    The main loop of the program. Runs forever (until program is closed).
    """
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    # If you need to do any initial work before starting the loop, this is a decent place to do that.
    
    # create variable to remember text between loops
    current_text = []
    scr_feed("MicroHydra REPL Ver 1.0.")
    scr_feed("Press GO Button to Exit.")
    scr_feed(">>>_")
    scr_show()
    
    
    while True: # Fill this loop with your program logic! (delete old code you dont need)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # put user input logic here
        
        # get list of newly pressed keys
        keys = kb.get_new_keys()
        
        # if there are keys, convert them to a string, and store for display
        if keys:
            if 'GO' in keys:
                machine.reset()
            if 'SPC' in keys:
                current_text.append(' ')
            elif 'BSPC' in keys:
                current_text = current_text[:-1]
            else:
                current_text += [i for i in keys if i != 'ENT']
            
            scr_buf[11] = ">>>" + ''.join(current_text) + "_"
            scr_show()
            
            if 'ENT' in keys:
                output_buffer.clear()
                try:
                    result = str(eval(''.join(current_text)))
                    if result != "None":
                        scr_buf[11] = scr_buf[11][:-1]
                        scr_feed(result.replace("\n","\\n"))
                    elif output_buffer.getvalue() != "":
                        result = output_buffer.getvalue()
                        output_buffer.clear()
                        scr_buf[11] = scr_buf[11][:-1]
                        scr_feed(result.replace("\n","\\n"))
                        
                except Exception as e:
                    try:
                        exec(''.join(current_text),globals())
                        result = output_buffer.getvalue()
                        output_buffer.clear()
                        if result != "":
                            scr_buf[11] = scr_buf[11][:-1]
                            scr_feed(result.replace("\n","\\n"))
                    except Exception as ee:
                        scr_feed(f"{ee}")
                       
                scr_feed(">>>_")
                scr_show()
                current_text = []
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # anything that needs to be done to prepare for next loop
        
        # do nothing for 10 milliseconds
        time.sleep_ms(10)


# start the main loop
try:
    main_loop()
except Exception as e:
    import sys
    with open('/log.txt', 'w') as f:
        f.write('[REPL]')
        sys.print_exception(e, f)
    
    tft.text(
            text=f"{e}",
            # center text on x axis:
            x=0, 
            y=0,
            color=config['ui_color']
            )
    tft.show()
