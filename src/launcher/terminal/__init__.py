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
config = Config()
kb = UserInput()

term = Terminal()

RTC = machine.RTC()


# --------------------------------------------------------------------------------------------------
# -------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
# --------------------------------------------------------------------------------------------------

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


def path_join(*args) -> str:
    """Join multiple paths together."""
    path = "/".join(args)
    # Remove any repeated slashes
    while "//" in path:
        path = path.replace("//", "/")
    if path.endswith("/") and len(path) > 1:
        path = path[:-1]
    return path


def path_split(path_str) -> tuple[str, str]:
    """Split last element off of path. (similar to os.path.split)."""
    # Early return on root dir
    if path_str == "/":
        return "/", ""

    *head, tail = path_str.split("/")
    head = path_join(*head)
    return head, tail


def strip_extension(path_str: str) -> str:
    """Strip the .py or .mpy from a file path."""
    return (
        path_str[:-3] if path_str.endswith('.py')
        else path_str[:-4] if path_str.endswith('.mpy')
        else path_str
    )
    


def find_py_path(name: str) -> str|None:
    """Try finding the given Python module name."""
    # look in current dir, then apps.
    for search_dir in (os.getcwd(), "/apps"):
        full_path = path_join(search_dir, name)
        
        if name in os.listdir(search_dir):
            if os.stat(full_path)[0] == 0x4000:  # is dir
                dir_files = os.listdir(full_path)
                if "__init__.py" in dir_files or "__init__.mpy" in dir_files:
                    # this is a module that can be imported!
                    return full_path
            elif name.endswith(".py" or name.endswith(".mpy")):
                return full_path
    return None
    


def execute_script(path, argv):
    """Import (or re-import) a given python module."""
    # sys.argv can't be assigned, (no `=`) but it can be modified.
    sys.argv.clear()
    sys.argv.extend(argv)
    print(path)
    # Override some globals so given script works with this terminal.
    glbls = globals().copy()
    glbls.update({'__name__': '__main__', 'print':term.print, 'input':custom_input})

    # clear module so it can be re-imported
    mod_name = strip_extension(path_split(path)[1])
    if mod_name in sys.modules:
        sys.modules.pop(mod_name)
    with open(path) as f:
        exec(f.read(), glbls, glbls)




# --------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """Run the main loop for the Terminal"""

    app_path = RTC.memory().decode()
    if len(app_path) > 0 and app_path[0] == '$':
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
                            result = commands[cmd](*args)
                            if result is not None:
                                term.print(result)
                        except Exception as e:
                            term.print(f"\033[91m{e}\033[0m")
                    else:
                        py_path = find_py_path(cmd)
                        if py_path is not None:
                            execute_script(py_path, args)
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
