"""MicroHydra App Template.

Version: 1.0


This is a basic skeleton for a MicroHydra app, to get you started.

There is no specific requirement in the way a MicroHydra app must be organized or styled.
The choices made here are based entirely on my own preferences and stylistic whims;
please change anything you'd like to suit your needs
(or ignore this template entirely if you'd rather)

This template is not intended to enforce a specific style, or to give guidelines on best practices,
it is just intended to provide an easy starting point for learners,
or provide a quick start for anyone that just wants to whip something up.

Have fun!

TODO: replace the above description with your own!
"""

import time

from lib import display, userinput
from lib.hydra import config


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_MH_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL_OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
DISPLAY = display.Display()

# object for accessing microhydra config (Delete if unneeded)
CONFIG = config.Config()

# object for reading keypresses (or other user input)
INPUT = userinput.UserInput()


# --------------------------------------------------------------------------------------------------
# -------------------------------------- function_definitions: -------------------------------------
# --------------------------------------------------------------------------------------------------

# Add any function definitions you want here
# def hello_world():
#     print("Hello world!")


# --------------------------------------------------------------------------------------------------
# ---------------------------------------- ClassDefinitions: ---------------------------------------
# --------------------------------------------------------------------------------------------------

# Add any class definitions you want here
# class Placeholder:
#     def __init__(self):
#         print("Placeholder")


# --------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """Run the main loop of the program.

    Runs forever (until program is closed).
    """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # If you need to do any initial work before starting the loop, this is a decent place to do it.

    # create variable to remember text between loops
    current_text = "Hello World!"



    while True:  # Fill this loop with your program logic! (delete old code you don't need)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # put user input logic here

        # get list of newly pressed keys
        keys = INPUT.get_new_keys()

        # if there are keys, convert them to a string, and store for display
        if keys:
            current_text = str(keys)


        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN GRAPHICS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # put graphics rendering logic here

        # clear framebuffer
        DISPLAY.fill(CONFIG.palette[2])

        # write current text to framebuffer
        DISPLAY.text(
            text=current_text,
            # center text on x axis:
            x=_DISPLAY_WIDTH_HALF - (len(current_text) * _CHAR_WIDTH_HALF),
            y=50,
            color=CONFIG.palette[8],
            )

        # write framebuffer to display
        DISPLAY.show()


        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # anything that needs to be done to prepare for next loop

        # do nothing for 10 milliseconds
        time.sleep_ms(10)



# start the main loop
main_loop()
