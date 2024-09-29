"""MicroHydra SHELL & Terminal.

A simple Terminal that can run console-based Apps.
Have fun!

TODO:
KFC V me 50
"""

import os
import time
import sys

import machine

from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
from lib.device import Device
from launcher.terminal.terminal import Terminal
from launcher.terminal.commands import get_commands

machine.freq(240_000_000)


_TERMINAL_VERSION = const("2.0")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_MH_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)
_MAX_CHARS = const(_MH_DISPLAY_WIDTH // _CHAR_WIDTH)

_LINE_HEIGHT = const(10)
_LINE_COUNT = const(_MH_DISPLAY_HEIGHT // _LINE_HEIGHT)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
tft = Display()

# object for accessing microhydra config (Delete if unneeded)
config = Config()

# object for reading keypresses
kb = UserInput()

# screen buffer
# scr_buf = [""]*_LINE_COUNT
term = Terminal()

RTC = machine.RTC()


# --------------------------------------------------------------------------------------------------
# -------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
# --------------------------------------------------------------------------------------------------

# def scr_feed(string):
#     """Shift each line up the screen by 1"""
#     for i in range(1, _LINE_COUNT):
#         scr_buf[i-1] = scr_buf[i]
#     scr_buf[-1] = string
# 
# 
# def scr_show():
#     """Show the terminal lines"""
#     # clear framebuffer
#     tft.fill(config['bg_color'])
#     # write current text to framebuffer
#     for i in range(_LINE_COUNT):
#         tft.text(text=scr_buf[i], x=0, y=_LINE_HEIGHT*i, color=config['ui_color'])
#     # write framebuffer to display
#     tft.show()


# def scr_clear():
#     """Erase all terminal lines"""
#     for i in range(_LINE_COUNT):
#         scr_buf[i] = ""
#     scr_show()


# # Custom print function that writes to the buffer
# def custom_print(*args, **kwargs):
#     """Print to terminal"""
#     str_out = (' '.join(map(str, args)) + kwargs.get('end', '')).split('\n')
#     for string in str_out:
#         while len(string) > _MAX_CHARS:
#             scr_feed(string[:_MAX_CHARS])
#             scr_show()
#             string = string[_MAX_CHARS:]
# 
#         scr_feed(string)
#         scr_show()
# 
# 
# # Replace the built-in print function with the custom one
# print = custom_print  # noqa: A001


# def custom_input(prmpt: str) -> str:
#     """Get user input (Override the `input` built-in)"""
#     print(f"{prmpt} _")
# 
#     current_text = []
#     while True:
#         keys = kb.get_new_keys()
#         # if there are keys, convert them to a string, and store for display
#         if keys:
#             if 'SPC' in keys:
#                 current_text.append(' ')
#             elif 'BSPC' in keys:
#                 current_text = current_text[:-1]
#             else:
#                 current_text += [i for i in keys if i != 'ENT']
# 
#             scr_buf[-1] = f"{prmpt} " + ''.join(current_text) + "_"
#             scr_show()
# 
#             if 'ENT' in keys or 'GO' in keys:
#                 scr_buf[-1] = scr_buf[-1][:-1]
#                 scr_show()
#                 return ''.join(current_text)

def custom_input(prmpt: str) -> str:
    """Get user input (Override the `input` built-in)"""
    term.print(f"{prmpt} _")

    current_text = []
    while True:
        keys = kb.get_new_keys()
        # if there are keys, convert them to a string, and store for display
        if keys:
            if 'SPC' in keys:
                current_text.append(' ')
            elif 'BSPC' in keys:
                current_text = current_text[:-1]
            else:
                current_text += [i for i in keys if i != 'ENT']

            scr_buf[-1] = f"{prmpt} " + ''.join(current_text) + "_"
            scr_show()

            if 'ENT' in keys or 'GO' in keys:
                scr_buf[-1] = scr_buf[-1][:-1]
                scr_show()
                return ''.join(current_text)


input = custom_input  # noqa: A001

def execute_script(path, argv):
    """Open and run a given python script."""
    # sys.argv can't be assigned, (no `=`) but it can be modified.
    sys.argv.clear()
    sys.argv.extend(argv)
    # Override some globals so given script works with this terminal.
    glbls = globals()
    glbls.update({'__name__': '__main__', 'print':term.print, 'input':custom_input})
    exec(open(path).read(), glbls)


# --------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """Run the main loop for the Terminal"""

    app_path = RTC.memory().decode()
    if len(app_path) > 0 and app_path[0] == '$':
        # TODO: Try replacing the below code with `__import__(app_path, globals=, locals=)`
        execute_script(app_path[1:], [])
    term.print(f"""\
\x1b[96;1mTerminal\x1b[22m v{_TERMINAL_VERSION}\x1b[36m,
with \x1b[96mMicroHydra v{'.'.join(str(x) for x in Device.mh_version)}\x1b[36m \
and \x1b[96mMicroPython v{os.uname().release}\x1b[36m, \
on \x1b[96m{os.uname().sysname}\x1b[36m.\x1b[0m\
""")
    term.print("\x1b[35mPress \x1b[1mopt\x1b[22m+\x1b[1mq\x1b[22m to quit.\x1b[0m")

    term.print()
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    redraw_counter = 0
    commands = get_commands(term)
    while True:

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        keys = kb.get_new_keys()

        for key in keys:
            if key == "ENT":
                inpt = term.submit_line().split()
                if inpt:
                    cmd, *args = inpt
                    if cmd in commands:
                        try:
                            commands[cmd](args)
                        except Exception as e:
                            term.print(f"\033[91m{e}\033[0m")
                    else:
                        term.print(f"\033[91mUnknown command: '{cmd}'\033[0m")
                
            else:
                term.type_key(key)
# 
#         if keys:
#             
#             if 'ENT' in keys:
#                 scr_buf[-1] = scr_buf[-1][:-1]
#                 try:
#                     args = (''.join(current_text)).split()
#                     if args:
#                         if args[0] == 'ls':
#                             term.print('  '.join(os.listdir() if len(args) == 1 else os.listdir(args[1])))
#                                 
#                         elif args[0] == 'cat':
#                             with open(args[1], 'r') as f:
#                                 term.print(f.read())
#                         elif args[0] == 'cd' or args[0] == 'chdir':
#                             os.chdir(args[1])
#                         elif args[0] == 'rm':
#                             for i in args[1:]:
#                                 os.remove(i)
#                         elif args[0] == 'touch':
#                             for i in args[1:]:
#                                 with open(i, 'w') as f:
#                                     f.write(i)
#                         elif args[0] == 'mv':
#                             os.rename(args[1],args[2])
#                         elif args[0] == 'cwd':
#                             term.print(os.getcwd())
#                         elif args[0] == 'mkdir':
#                             for i in args[1:]:
#                                 os.mkdir(i)
#                         elif args[0] == 'rmdir':
#                             for i in args[1:]:
#                                 os.rmdir(i)
#                         elif args[0] == 'uname':
#                             term.print(os.uname().machine)
#                         elif args[0] == 'clear':
#                             scr_clear()
#                         elif args[0] == 'reboot' or args[0] == 'exit':
#                             machine.reset()
#                         else:
#                             try:
#                                 if not '.py' in args[0]:
#                                     args[0] = args[0] + '.py'
#                                 if args[0] in os.listdir():
#                                     execute_script(args[0], args)
#                                 elif args[0] in os.listdir('/apps'):
#                                     execute_script(f"/apps/{args[0]}", args)
#                                 else:
#                                     term.print("Bad Command.")
#                             except Exception as e:
#                                 term.print(e)
#                                 term.print("Trying Hard Launch...")
#                                 cwd = os.getcwd()
#                                 if cwd != '/':
#                                     cwd += '/'
#                                 
#                                 RTC.memory(cwd + args[0])
#                                 # reset clock speed to default.
#                                 machine.freq(160_000_000)
#                                 time.sleep_ms(10)
#                                 machine.reset()
#                         
#                 except Exception as e:
#                     term.print(f"{e}")
#                        
#                 term.print(f"root@MH:{os.getcwd()}# _")
#                 current_text = []
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # do nothing for 10 milliseconds
        if redraw_counter == 50 or keys:
            redraw_counter = 0
            term.draw()
            tft.show()
        else:
            redraw_counter += 1
        time.sleep_ms(10)


# start the main loop
try:
    main_loop()
except Exception as e:
    tft.text(text=f"{e}", x=0, y=0, color=config['ui_color'])
    tft.show()

    time.sleep(1)
    raise
