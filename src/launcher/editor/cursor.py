"""A simple contianer to hold the user's cursor."""
import time


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

_FONT_HEIGHT = const(8)
_FONT_WIDTH = const(8)

_LINE_PADDING = const(2)
_FULL_LINE_HEIGHT = const(_LINE_PADDING + _FONT_HEIGHT)
_LINE_BG_HEIGHT = const(_FULL_LINE_HEIGHT - 1)


_STATUSBAR_HEIGHT = const(18)
_LINE_DRAW_START = const(_STATUSBAR_HEIGHT + _LINE_PADDING)


_CURSOR_BLINK_MS = const(1000)
_CURSOR_BLINK_HALF = const(_CURSOR_BLINK_MS // 2)


class Cursor:
    """The user's cursor."""

    def __init__(self):
        """Create a new cursor at 0,0."""
        self.x = 0
        self.y = 0


    def clamped(self, filelines, *, clamp_x=True) -> tuple[int, int]:
        """Return the cursor's x/y but clampped."""
        if 0 <= self.y < len(filelines):
            y = (
                0 if self.y < 0
                else len(filelines) - 1 if self.y >= len(filelines)
                else self.y
            )
        else:
            y = self.y
        if clamp_x and not (0 <= self.x < len(filelines[y])):
            x = (
                0 if self.x < 0
                else len(filelines[y]) - 1 if self.x >= len(filelines[y])
                else self.x
            )
        else:
            x = self.x
        return x, y


    def clamp_to_text(self, filelines, *, clamp_x=True):
        """Clamp cursor to file text."""
        self.x, self.y = self.clamped(filelines, clamp_x=clamp_x)


    def move(self, filelines, x=0, y=0):
        """Move the cursor."""
        if x:
            self.x += x
            self.clamp_to_text(filelines)
        if y:
            self.y += y
            self.clamp_to_text(filelines, clamp_x=False)


    def draw(self, display, filelines):
        """Draw the cursor."""
        display.rect(
            (self.x - filelines.display_x) * _FONT_WIDTH - 1,
            (self.y - filelines.display_y) * _FULL_LINE_HEIGHT + _LINE_DRAW_START,
            2, _FULL_LINE_HEIGHT,
            display.palette[4 if time.ticks_ms() % _CURSOR_BLINK_MS < _CURSOR_BLINK_HALF else 7],
        )
