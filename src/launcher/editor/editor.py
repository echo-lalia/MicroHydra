"""HyDE v2.x editor class."""
if __name__ == '__main__': from launcher import editor  # relative import for testing

import sys
import time
import machine

from .filelines import FileLines
from .displayline import DisplayLine
from .cursor import Cursor
from .undomanager import UndoManager

from esp32 import NVS
from lib.sdcard import SDCard
from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
from lib.hydra.statusbar import StatusBar
from lib.hydra.popup import UIOverlay
from lib.hydra import loader


# Statusbar stuff
_MH_DISPLAY_WIDTH = const(240)
_FONT_HEIGHT = const(8)
_FONT_WIDTH = const(8)

_STATUSBAR_HEIGHT = const(18)

_STATUSBAR_TEXT_Y = const((_STATUSBAR_HEIGHT - _FONT_HEIGHT) // 2)
_STATUSBAR_TEXT_X = const(4)
_STATUSBAR_TEXT_WIDTH = const((_MH_DISPLAY_WIDTH - _STATUSBAR_TEXT_X)//3 * 2)
_STATUSBAR_TEXT_CHARS = const(_STATUSBAR_TEXT_WIDTH // _FONT_WIDTH)


_DELETE_FLAG = const(0)
_INSERT_FLAG = const(1)


_ARROW_KEYS = {"LEFT", "RIGHT", "UP", "DOWN"}

# rare whitespace char is repurposed here to denote converted tab/space indents
_INDENT_SYM = const(' ')  # noqa: RUF001


# used for "exit to file browser" option:
# mh_if frozen:
# _FILE_BROWSER = const(".frozen/launcher/files")
# mh_else:
_FILE_BROWSER = const("/launcher/files")
# mh_end_if



# increased to full freq.
machine.freq(240_000_000)
# sd needs to be mounted for any files in /sd
SDCard().mount()



class Editor:
    """Main editor class."""

    def __init__(self):
        """Initialize HyDE."""
        self.display = Display()
        self.config = Config()
        self.overlay = UIOverlay()

        tokenizer.init(self.config)

        self.statusbar = StatusBar(register_overlay=False)
        self.inpt = UserInput(allow_locking_keys=True)

        self.cursor = Cursor()
        self.select_cursor = None
        self.clipboard = ""

        self.undomanager = UndoManager(self, self.cursor)

        self.lines = None

        self.filepath = None
        self.modified = False


    def open_file(self, filepath: str):
        """Open the given text file."""
        with open(filepath) as f:
            self.lines = FileLines(f.readlines())
        self.filepath = filepath


    def handle_move_selection(self, key):
        """Handle movement of selection cursor."""
        # Make a new selection cursor if one doesn't exist
        if self.select_cursor is None:
            self.select_cursor = Cursor()
            self.select_cursor.x = self.cursor.x
            self.select_cursor.y = self.cursor.y

        # Move the selection cursor
        if key == "LEFT":
            self.select_cursor.move(self.lines, x=-1)
        elif key == "RIGHT":
            self.select_cursor.move(self.lines, x=1)
        elif key == "UP":
            self.select_cursor.move(self.lines, y=-1)
        else: # key == "DOWN":
            self.select_cursor.move(self.lines, y=1)


    def file_options(self):
        """Give file options menu."""
        _OPTIONS = const(("Back", "Save", "Tab...", "Run...", "Exit..."))

        choice = self.overlay.popup_options(_OPTIONS, title="GO...")

        if choice == "Save":
            self.lines.save(self.filepath)
            self.modified = False
        elif choice == "Run...":
            self.run_options()
        elif choice == "Exit...":
            self.exit_options()
        elif choice == "Tab...":
            self.tab_options()


    def tab_options(self):
        """Give tab options menu."""
        title = "'tab' inserts tabs" if self.lines.use_tabs else "'tab' inserts spaces"
        _TAB_OPTIONS = const(("Back", "Use tabs", "Use spaces"))

        choice = self.overlay.popup_options(_TAB_OPTIONS, title=title, depth=1)
        nvs = NVS("editor")

        if choice == "Use tabs":
            self.lines.use_tabs = True
            nvs.set_i32("use_tabs", True)
            nvs.commit()

        elif choice == "Use spaces":
            self.lines.use_tabs = False
            nvs.set_i32("use_tabs", False)
            nvs.commit()


    def run_options(self):
        """Give run options submenu."""
        _RUN_OPTIONS = const(("Cancel", "Run here", "Restart and run"))
        choice = self.overlay.popup_options(_RUN_OPTIONS, title="Run...", depth=1)

        if choice == "Run here":
            self.run_file_here()
        elif choice == "Restart and run":
            self.boot_into_file(self.filepath)


    def exit_options(self):
        """Give exit options submenu."""
        _EXIT_OPTIONS = const(("Cancel", "Exit to Files", "Exit to Launcher"))

        choice = self.overlay.popup_options(_EXIT_OPTIONS, title="Exit...", depth=1)

        if choice == "Exit to Files":
            if self.modified:
                choice = self.overlay.popup_options(("Save", "Discard"), title="Save changes?")
                if choice == "Save":
                    self.lines.save(self.filepath)
            self.boot_into_file(_FILE_BROWSER)

        elif choice == "Exit to Launcher":
            choice = self.overlay.popup_options(("Save", "Discard"), title="Save changes?")
            if choice == "Save":
                self.lines.save(self.filepath)
            self.boot_into_file('')


    def boot_into_file(self, target_file):
        """Restart and load into target file."""
        self.overlay.draw_textbox("Restarting...")
        self.display.show()
        loader.launch_app(target_file)


    def run_file_here(self):
        """Try running the target file here."""
        self.lines.save(self.filepath)
        self.overlay.draw_textbox("Running...")
        self.display.show()
        try:
            # you have to slice off the ".py" to avoid importerror
            mod = __import__(filepath[:-3])
            # we need to unload the module to import it again later.
            mod_name = mod.__name__
            if mod_name in sys.modules:
                del sys.modules[mod_name]

        except Exception as e:  # noqa: BLE001
            self.overlay.error(f"File closed with error: {e}")



    def _delete_and_record_selection(self):
        """Delete (and record undo step for) any selected text."""
        if self.select_cursor is not None:
            self.undomanager.record(
                "insert",
                self.lines.get_selected_text(self.cursor, self.select_cursor),
                cursor=min(self.cursor, self.select_cursor),
            )
            self.lines.delete_selected_text(self.cursor, self.select_cursor)
        self.select_cursor = None
        self.modified = True


    def _insert_and_record(self, text):
        """Insert some text, and record an undo step for it."""
        self.lines.insert(text, self.cursor)
        self.undomanager.record("backspace", text)


    def handle_input(self, keys):  # noqa: PLR0912, PLR0915
        """Respond to user input."""
        mod_keys = self.inpt.get_mod_keys()

        for key in keys:
            if "CTL" in mod_keys:
                # CTRL kb commands
                if key == "LEFT":
                    self.cursor.jump(self.lines, x=-1)
                elif key == "RIGHT":
                    self.cursor.jump(self.lines, x=1)
                elif key == "UP":
                    self.cursor.move(self.lines, y=-5)
                elif key == "DOWN":
                    self.cursor.move(self.lines, y=5)


                # Undo/redo
                elif key == "z":
                    self.undomanager.undo()
                elif key in {'y', 'Z'}: # Allow both ctrl+y and ctrl+shift+z
                    self.undomanager.redo()


                # Save file
                elif key == "s":
                    self.lines.save(self.filepath)
                    self.modified = False


                # Clipboard
                elif key == "c":
                    if self.select_cursor is not None:
                        self.clipboard = self.lines.get_selected_text(self.cursor, self.select_cursor)

                elif key == "x":
                    if self.select_cursor is not None:
                        self.clipboard = self.lines.get_selected_text(self.cursor, self.select_cursor)
                        self.undomanager.record(
                            "insert",
                            self.clipboard,
                            cursor=min(self.cursor, self.select_cursor),
                        )
                        self.lines.delete_selected_text(self.cursor, self.select_cursor)
                        self.modified = True

                elif key == "v":
                    self._delete_and_record_selection()
                    # Chars have to be inserted individually so that line breaks work correctly.
                    # (in the future, it might be good to add a method for splitting text by newlines instead)
                    for char in self.clipboard:
                        self.lines.insert(char, self.cursor)
                    self.undomanager.record("backspace", self.clipboard)
                    self.select_cursor = None
                    self.modified = True


                elif key == "BSPC":
                    if self.select_cursor is not None:
                        self._delete_and_record_selection()
                    else:
                        self.cursor.jump(self.lines, x=-1, delete=True, undomanager=self.undomanager)
                    self.modified = True


            else:  # noqa: PLR5501
                # Normal keypress
                if key in _ARROW_KEYS:
                    # Directional input moves main, or selection cursor
                    if "SHIFT" in mod_keys:
                        self.handle_move_selection(key)
                    else:
                        self.select_cursor = None
                        if key == "LEFT":
                            self.cursor.move(self.lines, x=-1)
                        elif key == "RIGHT":
                            self.cursor.move(self.lines, x=1)
                        elif key == "UP":
                            self.cursor.move(self.lines, y=-1)
                        else: # key == "DOWN":
                            self.cursor.move(self.lines, y=1)


                elif key == "BSPC":
                    if self.select_cursor is not None:
                        self._delete_and_record_selection()
                    else:
                        # If we are at the start of the line, we should record a deleted line,
                        # otherwise just record the character before this one
                        if self.cursor.x == 0 and self.cursor.y > 0:
                            deleted_char = "\n"
                        else:
                            deleted_char = self.lines.get_char_left_of_cursor(self.cursor)
                        self.lines.backspace(self.cursor)
                        self.undomanager.record("insert", deleted_char)
                    self.modified = True


                elif key == self.inpt.aux_action:
                    self.file_options()


                elif key == "ENT":
                    # Line-break-specific logic
                    self._delete_and_record_selection()
                    # Get the current indentation level to automatically add indents
                    indentation = self.lines.get_indentation(self.cursor.y)
                    # If there is a colon to the left of the cursor, we should probably start an indented block.
                    if self.lines.get_char_left_of_cursor(self.cursor) == ":":
                        indentation += _INDENT_SYM
                    # Insert the line break, then any additional indentation
                    self._insert_and_record("\n")
                    self._insert_and_record(indentation)


                else:
                    # Normal char input
                    # Replace named keys with their input char
                    key = {
                        "SPC":" ",
                        "TAB":_INDENT_SYM,
                    }.get(key, key)

                    # Only insert single characters (filter other named keys)
                    if len(key) == 1:
                        self._delete_and_record_selection()
                        self._insert_and_record(key)



    def draw_statusbar(self):
        """Draw the statusbar with filepath."""
        # Draw statusbar base
        self.statusbar.draw(self.display)
        # blackout clock/text backing
        self.display.rect(
            _STATUSBAR_TEXT_X,
            _STATUSBAR_TEXT_Y,
            _STATUSBAR_TEXT_WIDTH,
            _FONT_HEIGHT,
            self.display.palette[4],
            fill=True,
        )

        # slice filepath to fit, and indicate a modified file
        filepath = self.filepath
        if self.modified:
            filepath += "*"

        if len(filepath) > _STATUSBAR_TEXT_CHARS:
            filepath = "..." + filepath[len(filepath) - (_STATUSBAR_TEXT_CHARS - 3):]

        # Draw text
        self.display.text(
            filepath,
            _STATUSBAR_TEXT_X,
            _STATUSBAR_TEXT_Y+1,
            self.display.palette[2]
        )
        self.display.text(
            filepath,
            _STATUSBAR_TEXT_X,
            _STATUSBAR_TEXT_Y,
            self.display.palette[7]
        )

        # Tell display to redraw keyboard overlays
        Display.draw_overlays = True


    def main(self):
        """Run the text editor."""

        self.display.fill(self.display.palette[2])
        self.lines.update_display_lines(self.cursor, force_update=True)
        self.lines.draw(self.display, self.cursor, self.select_cursor)
        self.draw_statusbar()

        while True:
            keys = self.inpt.get_new_keys()

            if keys:
                self.handle_input(keys)
                self.lines.draw(
                    self.display,
                    self.cursor,
                    self.select_cursor,
                    # self.select_cursor if self.select_cursor is not None else self.cursor,
                )
                # Draw selection if it exists:
                # if self.select_cursor is not None:
                #     self.cursor.draw_selection_cursor(self.select_cursor, self.display, self.lines)
                # Update statusbar
                self.draw_statusbar()

            else:
                if Display.draw_overlays:
                    # If the keyboard overlay is being drawn, we should probably redraw our statusbar.
                    self.draw_statusbar()
                # To smooth things out, we'll only insert a delay if we aren't redrawing the lines
                time.sleep_ms(50)

            if self.select_cursor is not None:
                self.select_cursor.draw(self.display, self.lines)
            self.cursor.draw(self.display, self.lines)
            self.display.show()




# Start editor:
filepath = loader.get_args()[0]
if not filepath:
    filepath = "/testeasing.py" # JUSTFORTESTING
#     filepath = "/apps/gameoflifemodified.py" # JUSTFORTESTING
#     filepath = "/testfile.py"

# Import a specific tokenizer depending on the file extension
if filepath.endswith(".py"):
    from .tokenizers import python as tokenizer
else:
    from .tokenizers import plaintext as tokenizer

# Pass the tokenizer to the DisplayLine
DisplayLine.tokenizer = tokenizer


# Create the editor
editor = Editor()

# Load the file and start the editor, but catch any errors to show on display (before raising)
try:
    editor.open_file(filepath)
    editor.main()
except Exception as e:
    editor.overlay.error(f"Editor encountered an error: {e}")
    raise
