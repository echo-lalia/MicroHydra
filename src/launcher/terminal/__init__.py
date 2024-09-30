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
from launcher.terminal.commands import get_commands, ctext

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
    glbls.update({'__name__': '__main__', 'print':term.print, 'input':term.input})

    # clear module so it can be re-imported
    mod_name = strip_extension(path_split(path)[1])
    if mod_name in sys.modules:
        sys.modules.pop(mod_name)
    with open(path) as f:
        exec(f.read(), glbls, glbls)

def exec_line(inpt, user_globals, term):
    # IDK why this dont work
    user_globals.update({'input':term.input, 'print':term.print})
    try:
        # so that output can be easily seen
        exec(f"print({inpt})", user_globals)
    except:
        exec(inpt, user_globals)

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
with MicroHydra v{'.'.join(str(x) for x in Device.mh_version)} \
and MicroPython v{os.uname().release}, \
on {os.uname().sysname}.
\x1b[35mPress \x1b[1mopt\x1b[22m+\x1b[1mq\x1b[22m to quit.\x1b[0m
""")
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    redraw_counter = 0
    commands = get_commands(term)
    user_globals = {}
    while True:

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        keys = kb.get_new_keys()

        for key in keys:
            if key == "ENT":
                inpt = term.submit_line()
                if inpt:
                    cmd, *args = inpt.split()
                    if cmd in commands:
                        try:
                            result = commands[cmd](*args)
                            if result is not None:
                                term.print(result)
                        except Exception as e:
                            term.print(ctext(repr(e), "RED"))
                    else:
                        py_path = find_py_path(cmd)
                        if py_path is not None:
                            try:
                                execute_script(py_path, args)
                            except Exception as e:
                                term.print(ctext(repr(e), "RED"))
                        else:
                            try:
                                exec_line(inpt, user_globals, term)
                            except ZeroDivisionError as e:
                                term.print(ctext(repr(e), "RED"))
                
            else:
                term.type_key(key)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if redraw_counter == 40 or keys:
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
