"""A container for lines from a text file."""
from launcher.editor.displayline import DisplayLine


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

_FONT_HEIGHT = const(8)
_FONT_WIDTH = const(8)

_LINE_PADDING = const(2)

_STATUSBAR_HEIGHT = const(18)
_SCROLLBAR_HEIGHT = const(3)

_NUM_DISPLAY_LINES = const(
    (_MH_DISPLAY_HEIGHT - _STATUSBAR_HEIGHT - _SCROLLBAR_HEIGHT - _LINE_PADDING)
    // (_FONT_HEIGHT + _LINE_PADDING)
)
_HORIZONTAL_CHARACTERS = const((_MH_DISPLAY_WIDTH // _FONT_WIDTH) - 1)



class FileLines:
    """A container class for lines of text.

    This class is responsible for storing plain lines of text,
    storing stylized display lines for text currently on-screen,
    and drawing/updating those display lines as the content changes.
    """

    def __init__(self, lines: list[str, ...]):
        """Create a FileLines from the given lines."""
        self.lines = lines
        self.display_lines = []
        self.display_idx = 0


    def __getitem__(self, idx: int) -> str:
        return self.lines[idx]


    def __setitem(self, idx: int, val: str):
        self.lines[idx] = val


    def draw(self, display, cursor):
        """Update display lines and draw them to the display."""

