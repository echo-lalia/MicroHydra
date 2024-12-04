"""A container for lines from a text file."""
if __name__ == '__main__': from launcher import editor  # relative import for testing
from .displayline import DisplayLine


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

_FONT_HEIGHT = const(8)
_FONT_WIDTH = const(8)

_LINE_PADDING = const(2)
_FULL_LINE_HEIGHT = const(_LINE_PADDING + _FONT_HEIGHT)

_STATUSBAR_HEIGHT = const(18)
_SCROLLBAR_HEIGHT = const(3)
_LINE_DRAW_START = const(_STATUSBAR_HEIGHT + _LINE_PADDING)

_NUM_DISPLAY_LINES = const(
    (_MH_DISPLAY_HEIGHT - _LINE_DRAW_START - _SCROLLBAR_HEIGHT)
    // _FULL_LINE_HEIGHT
)
_OVERDRAW_DISPLAY_LINES = const(_NUM_DISPLAY_LINES + 1)
_HORIZONTAL_CHARACTERS = const((_MH_DISPLAY_WIDTH // _FONT_WIDTH) - 1)

# Chars between cursor and edge of screen
_CURSOR_FOLLOW_PADDING = const(2)


# Scrollbar
_SCROLLBAR_WIDTH = const(3)
_SCROLLBAR_TOTAL_HEIGHT = const(_MH_DISPLAY_HEIGHT - _LINE_DRAW_START)
_SCROLLBAR_START_X = const(_MH_DISPLAY_WIDTH - _SCROLLBAR_WIDTH)
_SCROLLBAR_VLINE_X = const(_SCROLLBAR_START_X - 1)


# rare whitespace char is repurposed here to denote converted tab/space indents
_INDENT_SYM = const(' ')  # noqa: RUF001
_SPACE_INDENT = const('    ')
_TAB_INDENT = const('	')



class FileLines:
    """A container class for lines of text.

    This class is responsible for storing/accessing plain lines of text,
    storing stylized display lines for text currently on-screen,
    and drawing/updating those display lines as the content changes.
    """

    def __init__(self, lines: list[str, ...]):
        """Create a FileLines from the given lines."""
        for idx, line in enumerate(lines):
            lines[idx] = self._clean_line(line)

        self.lines = lines
        self.display_lines = {}
        self.display_y = -2
        self.display_x = 0


    @staticmethod
    def _replace_tabs(line: str) -> str:
        """Replace tabs with fake tab."""
        tab_syms = ''
        while line.startswith(_TAB_INDENT):
            line = line[1:]
            tab_syms += _INDENT_SYM
        return tab_syms + line


    @staticmethod
    def _replace_space_indents(line: str) -> str:
        """Replace space indents with fake tab."""
        space_syms = ''
        while line.startswith(' '):
            # we must handle cases where less than 4 spaces are used, but we expect 4.
            for _ in range(4):
                if line.startswith(' '):
                    line = line[1:]
            space_syms += _INDENT_SYM
        return space_syms + line


    def _clean_line(self, line) -> str:
        """Remove line breaks and indentation."""
        return self._replace_space_indents(
            self._replace_tabs(
                line.replace("\r", "").replace("\n", "")
            )
        )


    def __len__(self):
        return len(self.lines)


    def __getitem__(self, idx: int) -> str:
        return self.lines[idx]


    def __setitem__(self, idx: int, val: str):
        self.lines[idx] = val


    def get_char_at_cursor(self, cursor) -> str:
        """Get the char at the current cursor position."""
        if 0 <= cursor.y < len(self.lines) \
        and 0 <= cursor.x < len(self.lines[cursor.y]):
            return self.lines[cursor.y][cursor.x]
        return ""


    def update_display_lines(self, cursor, *, force_update=False):
        """Update display lines to reflect current y viewport."""

        # Clamp display y to cursor (Make display follow cursor)
        view_moved = False
        start_y = self.display_y
        # if cursor is above display, move display up
        if cursor.y < start_y:
            start_y = cursor.y
            view_moved = True

        # If cursor is below display, move display down
        if cursor.y >= start_y + _NUM_DISPLAY_LINES:
            start_y = cursor.y - _NUM_DISPLAY_LINES + 1
            view_moved = True

        self.display_y = start_y


        # Clamp display x to cursor (Make display follow cursor)
        if cursor.x - _CURSOR_FOLLOW_PADDING < self.display_x:
            self.display_x = max(cursor.x - _CURSOR_FOLLOW_PADDING, 0)
        elif cursor.x - _HORIZONTAL_CHARACTERS + _CURSOR_FOLLOW_PADDING > self.display_x:
            self.display_x = cursor.x - _HORIZONTAL_CHARACTERS + _CURSOR_FOLLOW_PADDING


        if view_moved or force_update:
            # Remake self.display_lines to reflect current view
            # (reusing display lines we already have)
            old_lines = self.display_lines
            self.display_lines = {}
            # _OVERDRAW_DISPLAY_LINES is _NUM_DISPLAY_LINES + 1
            # This adds an extra display line to fill out the bottom of the screen
            for i in range(_OVERDRAW_DISPLAY_LINES):
                line_y = start_y + i

                # Set display line
                self.display_lines[line_y] = (
                    # use old line if it exists
                    old_lines[line_y] if line_y in old_lines
                    # Make a new line, and use the file line if it exists
                    else DisplayLine(self.lines[line_y] if 0 <= line_y < len(self.lines) else "")
                )


    def draw(self, display, cursor):
        """Update display lines and draw them to the display."""
        self.update_display_lines(cursor)

        y = _LINE_DRAW_START
        for i in range(self.display_y, self.display_y + _OVERDRAW_DISPLAY_LINES):
            line = self.display_lines[i]
            line.draw(
                display,
                self.display_x * -_FONT_WIDTH, y,
                selected=(i == cursor.y),
            )
            y += _FULL_LINE_HEIGHT

        # Draw scrollbar
        display.vline(_SCROLLBAR_VLINE_X, _LINE_DRAW_START, _SCROLLBAR_TOTAL_HEIGHT, display.palette[2])
        display.rect(
            _SCROLLBAR_START_X, _LINE_DRAW_START,
            _SCROLLBAR_WIDTH, _SCROLLBAR_TOTAL_HEIGHT,
            display.palette[1], fill=True,
        )
        scrollbar_start = max(
            (self.display_y * _SCROLLBAR_TOTAL_HEIGHT) // len(self) + _LINE_DRAW_START,
            _LINE_DRAW_START,
        )
        scrollbar_end = max(
            ((self.display_y + _NUM_DISPLAY_LINES) * _SCROLLBAR_TOTAL_HEIGHT) // len(self) + _LINE_DRAW_START,
            scrollbar_start,
        ) + 1
        display.rect(
            _SCROLLBAR_START_X, scrollbar_start,
            _SCROLLBAR_WIDTH, scrollbar_end - scrollbar_start,
            display.palette[4], fill=True,
        )

