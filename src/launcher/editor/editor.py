"""HyDE v2.x editor class."""
import time

from .filelines import FileLines
from .displayline import DisplayLine
from .cursor import Cursor

from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
from lib.hydra.statusbar import StatusBar
from lib.hydra import loader



class Editor:
    """Main editor class."""

    def __init__(self):
        self.display = Display()
        self.config = Config()
        self.statusbar = StatusBar()
        self.inpt = UserInput(allow_locking_keys=True)

        self.cursor = Cursor()
        self.select_cursor = None

        self.lines = None


    def open_file(self, filepath: str):
        """Open the given text file."""
        with open(filepath, "r") as f:
            self.lines = FileLines(f.readlines())


    def handle_input(self, keys):
        """Respond to user input."""
        for key in keys:
            if key == "RIGHT":
                self.cursor.move(self.lines, x=1)
            elif key == "LEFT":
                self.cursor.move(self.lines, x=-1)
            elif key == "UP":
                self.cursor.move(self.lines, y=-1)
            elif key == "DOWN":
                self.cursor.move(self.lines, y=1)



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
