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
    
    
    def __init__(self):
        self.display = Display()
        self.config = Config()
        self.inpt = UserInput(allow_locking_keys=True)
        self.statusbar = StatusBar()

        self.cursor = Cursor()
        self.select_cursor = None

        self.lines = None


    def open_file(self, filepath: str):
        """Open the given text file."""
        with open(filepath, "r") as f:
            self.lines = FileLines(f.readlines())


    def main(self):
        """Run the text editor."""
        
        self.display.fill(self.display.palette[2])

        while True:
            keys = self.inpt.get_new_keys()

            self.lines.draw(self.display, self.cursor)
            self.display.show()

            time.sleep_ms(50)



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
