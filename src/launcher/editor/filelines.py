"""A container for lines from a text file."""
if __name__ == '__main__': from launcher import editor  # relative import for testing
from .displayline import DisplayLine

from esp32 import NVS


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

_FONT_HEIGHT = const(8)
_FONT_WIDTH = const(8)

_LINE_PADDING = const(2)
_FULL_LINE_HEIGHT = const(_LINE_PADDING + _FONT_HEIGHT)

_LEFT_PADDING = const(4)

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

        self.use_tabs = self._set_indentation_mode()


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


    def _set_indentation_mode(self) -> bool:
        """Return True if file should use tabs (rather than spaces) based on file OR preference."""
        # Check file for an existing indentation type
        for line in self.lines:
            if line.startswith(_SPACE_INDENT):
                return False
            if line.startswith(_TAB_INDENT):
                return True

        # If no indentation exists in the file, set based on user preference.
        nvs = NVS("editor")
        try:
            # Use the set value if it exists
            return bool(nvs.get_i32("use_tabs"))
        except OSError:
            # (Otherwise, set to False as a default, and return
            nvs.set_i32("use_tabs", False)
            nvs.commit()
        return False


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
        """Get values from self.lines, defaulting to an empty string."""
        return self.lines[idx] if (0 <= idx < len(self.lines)) else ""


    def __setitem__(self, idx: int, val: str):
        self.lines[idx] = val


    def save(self, filepath: str):
        """Save the file lines to the given filepath."""
        indent = _TAB_INDENT if self.use_tabs else _SPACE_INDENT

        with open(filepath, "w") as f:
            for line in self.lines:
                # Replace the tab characters (based on preference) and add line breaks
                f.write(
                    line.replace(_INDENT_SYM, indent) + "\n",
                )


    def get_indentation(self, y: int) -> str:
        """Return the indentation for the given line index."""
        line = self[y]
        indentation = ""
        while line.startswith(_INDENT_SYM):
            indentation += _INDENT_SYM
            line = line[1:]
        return indentation


    def get_char_at_cursor(self, cursor) -> str:
        """Get the char at the current cursor position."""
        if 0 <= cursor.y < len(self.lines) \
        and 0 <= cursor.x < len(self.lines[cursor.y]):
            return self.lines[cursor.y][cursor.x]
        return ""


    def get_char_left_of_cursor(self, cursor) -> str:
        """Get the char to the left of the cursor."""
        if cursor.x == 0 and cursor.y == 0:
            return ""

        cursor.move(self, x=-1)
        out = self.get_char_at_cursor(cursor)
        cursor.move(self, x=1)
        return out


    def _insert_line(self, cursor):
        """Insert one line at the cursor."""
        # Split current line at cursor
        new_line = self[cursor.y][cursor.x:]
        self[cursor.y] = self[cursor.y][:cursor.x]
        # Insert second half of line after cursor
        self.lines.insert(cursor.y + 1, new_line)
        # Move cursor to the right, which should put us on the new line
        cursor.move(self, x=1)
        # Update the display for the previous index, and all indices after
        for key in self.display_lines:
            if key >= cursor.y - 1:
                self.display_lines[key] = DisplayLine(self[key])


    def get_selected_text(self, cursor, select_cursor) -> str:
        """Get the text between the cursor and select_cursor."""
        # Start by determining which cursor comes first
        start_cursor = min(cursor, select_cursor)
        end_cursor = max(cursor, select_cursor)

        selected_text = ""
        # Iterate over each line between each cursor, adding the contents to the selected text.
        for y in range(start_cursor.y, end_cursor.y + 1):
            this_line = self[y]
            start_x = start_cursor.x if start_cursor.y == y else 0
            end_x = end_cursor.x if end_cursor.y == y else len(this_line)

            # add the line to the selection, along with a line break
            selected_text += this_line[start_x: end_x] + "\n"

        # remove any final trailing linebreak
        if selected_text.endswith("\n"):
            selected_text = selected_text[:-1]

        return selected_text


    def delete_selected_text(self, cursor, select_cursor):
        """Delete all text between cursor and select_cursor."""
        # Start by determining which cursor comes first
        start_cursor = min(cursor, select_cursor)
        end_cursor = max(cursor, select_cursor)

        # Delete text until end_cursor reaches start_cursor
        while end_cursor > start_cursor:
            self.backspace(end_cursor)


    def insert(self, text: str, cursor):
        """Insert text at the cursor."""
        cursor.clamp_to_text(self)
        # Insert a new line, or just insert text on this line
        if text == "\n":
            self._insert_line(cursor)
        else:
            self[cursor.y] = self[cursor.y][:cursor.x] + text + self[cursor.y][cursor.x:]
            # Place cursor at right of inserted text
            cursor.move(self, x=len(text))
            # Update the display line
            self.display_lines[cursor.y] = DisplayLine(self.lines[cursor.y])


    def backspace(self, cursor):
        """Backspace once."""
        cursor.clamp_to_text(self)

        if cursor.x != 0:  # Delete normal text
            self[cursor.y] = self[cursor.y][:cursor.x - 1] + self[cursor.y][cursor.x:]
            # Move cursor to account for modified text
            cursor.move(self, x=-1)
            # Update the display line
            self.display_lines[cursor.y] = DisplayLine(self.lines[cursor.y])

        elif cursor.y > 0:  # Delete line break
            # Move cursor left, onto end of previous line
            cursor.move(self, x=-1)
            # Append current line onto previous line, and delete current line
            self[cursor.y] += self.lines.pop(cursor.y + 1)
            # Update the display for this index, and all indices after
            for key in self.display_lines:
                if key >= cursor.y:
                    self.display_lines[key] = DisplayLine(self[key])


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
                    else DisplayLine(self[line_y])
                )


    def draw(self, display, cursor, select_cursor):
        """Update display lines and draw them to the display."""
        self.update_display_lines(cursor if select_cursor is None else select_cursor)

        # Draw each line
        y = _LINE_DRAW_START
        for line_idx in range(self.display_y, self.display_y + _OVERDRAW_DISPLAY_LINES):
            line = self.display_lines[line_idx]

            # Determine if line has a highlighted selection
            if select_cursor is None:
                # No highlight if there is no selection
                highlight = None
            else:
                # There is a selection to highlight. Start by finding which cursor comes first.
                start_cursor = min(cursor, select_cursor)
                end_cursor = max(cursor, select_cursor)

                if line_idx == start_cursor.y:
                    # Highlight from start cursor to end cursor (or end of line)
                    highlight = (
                        start_cursor.x,
                        end_cursor.x if start_cursor.y == end_cursor.y else len(self[line_idx]),
                    )

                elif start_cursor.y < line_idx < end_cursor.y:
                    # this line is between the cursors. Highlight the whole thing.
                    highlight = (
                        0,
                        min(len(self[line_idx]), 1),
                    )

                elif line_idx == end_cursor.y:
                    # This is the final line to highlight. Highlight from start of line to end_cursor
                    highlight = (0, end_cursor.x)

                else:
                    # This line is not inside the selection.
                    highlight = None

            # Draw the line
            line.draw(
                display,
                self.display_x * -_FONT_WIDTH, y,
                selected=(line_idx == (cursor.y if select_cursor is None else select_cursor.y)),
                highlight=highlight,
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
