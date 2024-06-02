from lib import st7789fbuf, mhconfig, keyboard
import machine, time

"""
MicroHydra App Template
Version: 1.0


This is a basic skeleton for a MicroHydra app, to get you started.

There is no specific requirement in the way a MicroHydra app must be organized or styled.
The choices made here are based entirely on my own preferences and stylistic whims;
please change anything you'd like to suit your needs (or ignore this template entirely if you'd rather)

This template is not intended to enforce a specific style, or to give guidelines on best practices,
it is just intended to provide an easy starting point for learners,
or provide a quick start for anyone that just wants to whip something up.

Have fun!

TODO: replace the above description with your own!
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


#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

# Add any function definitions you want here
# def hello_world():
#     print("Hello world!")


#--------------------------------------------------------------------------------------------------
#--------------------------------------- CLASS DEFINITIONS: ---------------------------------------
#--------------------------------------------------------------------------------------------------

# Add any class definitions you want here
# class Placeholder:
#     def __init__(self):
#         print("Placeholder")




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
    current_text = "Hello World!" 
    
    
    
    while True: # Fill this loop with your program logic! (delete old code you dont need)
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # put user input logic here
        
        # get list of newly pressed keys
        keys = kb.get_new_keys()
        
        # if there are keys, convert them to a string, and store for display
        if keys:
            current_text = str(keys)
        
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN GRAPHICS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # put graphics rendering logic here
        
        # clear framebuffer 
        tft.fill(config['bg_color'])
        
        # write current text to framebuffer
        tft.text(
            text=current_text,
            # center text on x axis:
            x=_DISPLAY_WIDTH_HALF - (len(current_text) * _CHAR_WIDTH_HALF), 
            y=50,
            color=config['ui_color']
            )
        
        # write framebuffer to display
        tft.show()
        
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # anything that needs to be done to prepare for next loop
        
        # do nothing for 10 milliseconds
        time.sleep_ms(10)


# start the main loop
main_loop()