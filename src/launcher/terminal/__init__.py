"""MicroHydra SHELL & Terminal.

A simple Terminal that can run console-based apps,
execute some commands, and function as a basic REPL.

Have fun!
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



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_TERMINAL_VERSION = const("2.0")

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
            elif name.endswith(".py") or name.endswith(".mpy"):
                return full_path
    return None


def execute_script(path, argv):
    """Import (or re-import) a given python module."""
    # sys.argv can't be assigned, (no `=`) but it can be modified.
    sys.argv.clear()
    sys.argv.extend(argv)
    # Override some globals so given script works with this terminal.
    glbls = {'__name__': '__main__', 'print':term.print, 'input':term.input}

    # clear module so it can be re-imported
    mod_name = strip_extension(path_split(path)[1])
    if mod_name in sys.modules:
        sys.modules.pop(mod_name)
    with open(path) as f:
        exec(f.read(), glbls, glbls)  # noqa: S102


def _is_printable(inpt:str) -> bool:
    """Check if given code is a simple/printable statement.

    A printabe statement shouldn't have any operators or newlines,
    like '=', ';' ':', or '/n', outside of quotes or brackets.
    """
    banned_chars = {"=", ":", ";", "\n"}

    # early return if none of the offending symbols are in the code
    if not any(ch in inpt for ch in banned_chars):
        return True
    # Iterate through inpt, tracking quotes and brackets,
    # to determine whether or not the banned chars are outside strings/brackets.
    quotes = None    # Current string quote character.
    bracket_lvl = 0  # Depth of bracket nesting.
    while inpt:
        ch = inpt[0]
        # NOT a printable string
        if ch in banned_chars \
        and quotes is None \
        and bracket_lvl == 0:
            return False

        # track brackets
        if ch in {"{", "[", "("}:
            bracket_lvl += 1
        elif ch in {")", "]", "}"}:
            bracket_lvl -= 1

        # track quotes
        elif ch in {'"', "'"}:
            frst3 = inpt[:3]
            if quotes is None and frst3 in {'"""', "'''"}:
                quotes = frst3
            elif quotes in {frst3, ch}:
                quotes = None

        inpt = inpt[1:]
    return True


def exec_line(inpt: str, user_globals: dict, term: Terminal):
    """Try interactively executing the given code."""
    user_globals.update({'input':term.input, 'print':term.print})
    try:
        # so that output can be easily seen
        exec(  # noqa: S102
            f"print(repr({inpt}),skip_none=True)" if _is_printable(inpt) else inpt,
            user_globals,
            user_globals,
        )
    except:
        exec(inpt, user_globals, user_globals)  # noqa: S102


# --------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """Run the main loop for the Terminal."""

    app_path = RTC.memory().decode()
    if len(app_path) > 0 and app_path[0] == '$':
        execute_script(app_path[1:], [])
    term.print(f"""\
\x1b[96;1mTerminal\x1b[22m v{_TERMINAL_VERSION}\x1b[36m,
with MicroHydra v{'.'.join(str(x) for x in Device.mh_version)} \
and MicroPython v{os.uname().release}, \
on {os.uname().sysname}.
\x1b[35mPress \x1b[1mopt\x1b[22m+\x1b[1mq\x1b[22m to quit.
Type \x1b[1mhelp\x1b[22m to print a help message.\x1b[0m
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
                if inpt and not inpt.isspace():
                    cmd, *args = inpt.split()
                    if cmd in commands:
                        try:
                            result = commands[cmd](*args)
                            if result is not None:
                                term.print(result)
                        except Exception as e:  # noqa: BLE001
                            term.print(ctext(repr(e), "RED"))
                    else:
                        py_path = find_py_path(cmd)
                        if py_path is not None:
                            try:
                                execute_script(py_path, args)
                            except Exception as e:  # noqa: BLE001
                                term.print(ctext(repr(e), "RED"))
                        else:
                            try:
                                exec_line(inpt, user_globals, term)
                            except Exception as e:  # noqa: BLE001
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
    tft.text(text=f"{e}", x=0, y=0, color=config.palette[11])
    tft.show()

    time.sleep(1)
    raise
