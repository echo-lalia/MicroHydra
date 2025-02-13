"""HyDE v2.x editor class."""
if __name__ == '__main__': from launcher import editor  # relative import for testing

import time

from .filelines import FileLines
from .displayline import DisplayLine
from .cursor import Cursor
from .undomanager import UndoManager

from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
from lib.hydra.statusbar import StatusBar
from lib.hydra import loader



_DELETE_FLAG = const(0)
_INSERT_FLAG = const(1)



class Editor:
    """Main editor class."""

    def __init__(self):
        """Initialize HyDE."""
        self.display = Display()
        self.config = Config()
        self.statusbar = StatusBar()
        self.inpt = UserInput(allow_locking_keys=True)

        self.cursor = Cursor()
        self.select_cursor = None

        self.undomanager = UndoManager(self, self.cursor)

        self.lines = None


    def open_file(self, filepath: str):
        """Open the given text file."""
        with open(filepath, "r") as f:
            self.lines = FileLines(f.readlines())


    def handle_input(self, keys):  # noqa: PLR0912
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

                elif key == "BSPC":
                    self.cursor.jump(self.lines, x=-1, delete=True, undomanager=self.undomanager)

            else:  # noqa: PLR5501
                # Normal keypress
                if key == "LEFT":
                    self.cursor.move(self.lines, x=-1)
                elif key == "RIGHT":
                    self.cursor.move(self.lines, x=1)
                elif key == "UP":
                    self.cursor.move(self.lines, y=-1)
                elif key == "DOWN":
                    self.cursor.move(self.lines, y=1)

                elif key == "BSPC":
                    # If we are at the start of the line, we should record a deleted line,
                    # otherwise just record the character before this one
                    if self.cursor.x == 0 and self.cursor.y > 0:
                        deleted_char = "\n"
                    else:
                        deleted_char = self.lines.get_char_left_of_cursor(self.cursor)
                    self.lines.backspace(self.cursor)
                    self.undomanager.record("insert", deleted_char)

                elif key == "ENT":
                    self.lines.insert("\n", self.cursor)
                    self.undomanager.record("backspace", "\n")

                elif key == "SPC":
                    self.lines.insert(" ", self.cursor)
                    self.undomanager.record("backspace", " ")

                elif len(key) == 1:
                    # Normal char input
                    self.lines.insert(key, self.cursor)
                    self.undomanager.record("backspace", key)



    def main(self):
        """Run the text editor."""

        self.display.fill(self.display.palette[2])
        self.lines.update_display_lines(self.cursor, force_update=True)
        self.lines.draw(self.display, self.cursor)

        while True:
            keys = self.inpt.get_new_keys()

            if keys:
                self.handle_input(keys)
                self.lines.draw(self.display, self.cursor)
            else:
                # To smooth things out, we'll only insert a delay if we aren't redrawing the lines
                time.sleep_ms(50)

            self.cursor.draw(self.display, self.lines)
            self.display.show()




# Start editor:
filepath = loader.get_args()[0]
if not filepath:
    filepath = "/teststatusbar.py" # JUSTFORTESTING

# Import a specific tokenizer depending on the file extension
# TESTING: just use default for now
from .tokenizers import plaintext as tokenizer
DisplayLine.tokenizer = tokenizer

editor = Editor()
editor.open_file(filepath)
editor.main()
