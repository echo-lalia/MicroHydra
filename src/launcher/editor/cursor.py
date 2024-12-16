"""A simple contianer to hold the user's cursor."""
if __name__ == '__main__': from launcher import editor  # relative import for testing

import time


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

_FONT_HEIGHT = const(8)
_FONT_WIDTH = const(8)

_LINE_PADDING = const(2)
_FULL_LINE_HEIGHT = const(_LINE_PADDING + _FONT_HEIGHT)
_LINE_BG_HEIGHT = const(_FULL_LINE_HEIGHT - 1)

_LEFT_PADDING = const(4)

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

    @staticmethod
    @micropython.viper
    def _classify_char(char) -> int:
        """Return an arbitrary integer classification for a given character."""
        if not char:  # empty string
            return 0

        ch = int(ord(char))
        if 9 <= ch <= 32:    # space
            return 1
        if 48 <= ch <= 57:   # numeric
            return 2
        if 65 <= ch <= 122:  # alphabet
            return 3
        if 33 <= ch <= 126:  # ansi symbols
            return 4
        return 5  # Other


    def jump(self, filelines, x: int, *, delete: bool = False):
        """Move left or right until we hit a new character type."""
        # When moving left, we need the key to the left of the cursor
        get_char = filelines.get_char_left_of_cursor if x == -1 else filelines.get_char_at_cursor

        start_class = self._classify_char(get_char(self))
        for _ in range(100):  # arbitrary limit
            # If `delete`, then keep backspace until hitting a new char.
            # Otherwise just move in the specified direction
            if delete:
                filelines.backspace(self)
            else:
                self.move(filelines, x=x)

            if (# Exit when we hit a new character type
                self._classify_char(get_char(self)) != start_class
                # Exit if we hit the start of the file
                or (self.y == 0 and self.x == 0)
                # Exit if we hit the end of the file
                or (x != -1 and self.y == len(filelines) - 1 and self.x == len(filelines[self.y]))
            ):
                return


    def clamped(self, filelines, *, clamp_x=True) -> tuple[int, int]:
        """Return the cursor's x/y clamped to the filelines."""
        if not 0 <= self.y < len(filelines):
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
                else len(filelines[y]) if self.x > len(filelines[y])
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
            # Handle line wrapping on start/ends of lines
            if x > 0 and self.x >= len(filelines[self.y]) \
            and self.y < len(filelines) - 1:
                # When at the end of a line,
                # moving right puts us at the start of the next line.
                self.x = 0
                self.y += 1
            elif x < 0 and self.x <= 0 \
            and self.y > 0:
                # When at the start of a line,
                # moving left will put us at the end of the previous line.
                self.y -= 1
                self.x = len(filelines[self.y])
            else:
                # When not at the start or end of line,
                # we can just move x some distance.
                self.x += x

            self.clamp_to_text(filelines)

        if y:
            self.y += y
            # Handle jumping to start/end of line, and moving display at the start/end of file
            if self.y < 0:
                self.x = 0
                filelines.display_y -= 1
                filelines.update_display_lines(self, force_update=True)
            elif self.y >= len(filelines):
                self.x = len(filelines[len(filelines) - 1])
                filelines.display_y += 1
                filelines.update_display_lines(self, force_update=True)

            self.clamp_to_text(filelines, clamp_x=False)


    def draw(self, display, filelines):
        """Draw the cursor."""
        display.vline(
            (self.x - filelines.display_x) * _FONT_WIDTH + _LEFT_PADDING,
            (self.y - filelines.display_y) * _FULL_LINE_HEIGHT + _LINE_DRAW_START,
            _FULL_LINE_HEIGHT,
            display.palette[4 if time.ticks_ms() % _CURSOR_BLINK_MS < _CURSOR_BLINK_HALF else 7],
        )
