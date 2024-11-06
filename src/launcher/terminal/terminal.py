"""Terminal class to write and display to."""
from lib.display import Display
from lib.userinput import UserInput
from launcher.terminal.termline import TermLine
from lib.hydra.utils import get_instance
import time
import os

_MH_DISPLAY_WIDTH = const(240)
_MH_DISPLAY_HEIGHT = const(135)

_NUM_PRINT_LINES = const(_MH_DISPLAY_HEIGHT // 11)
_PRINT_LINE_START = const(_MH_DISPLAY_HEIGHT - 12 - (_NUM_PRINT_LINES * 11))
_USER_LINE_HEIGHT = const(12)
_USER_LINE_Y_FILL = const(_MH_DISPLAY_HEIGHT - _USER_LINE_HEIGHT)
_USER_LINE_Y = const(_MH_DISPLAY_HEIGHT - 11)
_MAX_TEXT_WIDTH = const(_MH_DISPLAY_WIDTH // 8)

_CURSOR_BLINK_MS = const(500)
_CURSOR_BLINK_MOD = const(_CURSOR_BLINK_MS * 2)

_MAX_STORED_LINES = const(5)


def disp_len(text: str) -> int:
    """Calculate the real length of text with only displayable characters."""
    # strip style escape codes from text
    while "\033[" in text and "m" in text:
        esc_start = text.index("\033[")
        post_esc_text = text[esc_start:]
        if "m" in post_esc_text:
            text = text[:esc_start] + text[text.index("m", esc_start) + 1:]
        else:
            # "m" could be before the escape character and not after.
            text = text.replace("\033[", "", 1)
    return len(text)


class Terminal:
    """Graphical terminal, for printing to."""

    def __init__(self):
        """Create the terminal."""
        self.lines = [TermLine('')] * _NUM_PRINT_LINES
        self.prev_lines = []
        self.current_line = ''
        self.display = get_instance(Display, allow_init=False)
        self.user_input = get_instance(UserInput, allow_init=False)
        self.lines_changed = False


    def clear(self):
        """Clear printed lines."""
        self.lines = [TermLine('')] * _NUM_PRINT_LINES


    @staticmethod
    def split_lines(text:str) -> list[str]:
        """Split a string into multiple lines, based on max line-length."""
        # First split on newlines
        inpt_lns = text.split("\n")
        outpt_lns = []
        for inpt_ln in inpt_lns:
            # Split each line by length
            lines = []
            current_line = ''
            words = inpt_ln.split()

            for word in words:
                # Single word too long for display (split mid-word)
                while disp_len(word) >= _MAX_TEXT_WIDTH:
                    lines.append(current_line)
                    current_line = word[:_MAX_TEXT_WIDTH]
                    word = word[_MAX_TEXT_WIDTH:]
                # Word + line too long for display (split on whitespace)
                if disp_len(word) + disp_len(current_line) >= _MAX_TEXT_WIDTH:
                    lines.append(current_line)
                    current_line = word
                # add first word with no leading space
                elif disp_len(current_line) == 0:
                    current_line += word
                # add a space and the current word
                else:
                    current_line += ' ' + word

            lines.append(current_line) # add final line
            outpt_lns += lines
        return outpt_lns


    def print(self, *args, skip_none=False, **kwargs):  # noqa: ARG002
        """Print to the terminal. Intended to be compatible with the `print` built-in.

        Currently does not support `print`s kwargs.
        """
        text = ' '.join(str(arg) for arg in args)
        if skip_none and text == "None":
            return
        print(*args)
        lines = self.split_lines(text)
        for line in lines:
            self.lines.append(TermLine(line))
            self.lines.pop(0)
        self.lines_changed = True
        self.draw()
        self.display.show()

    def input(self, prmpt: str = '') -> str:
        """Get user input (Override the `input` built-in)."""

        current_text = ''
        count = 50
        while True:
            keys = self.user_input.get_new_keys()
            # if there are keys, convert them to a string, and store for display
            for key in keys:
                if key == 'SPC':
                    current_text += ' '
                elif key == 'BSPC':
                    current_text = current_text[:-1]
                elif key == 'ENT':
                    self.draw()
                    self.display.show()
                    return current_text
                elif len(key) == 1:
                    current_text += key

            if keys or count == 50:
                count = 0
                self._draw_user_text(prmpt, current_text)
                self.display.show()


    def type_key(self, key):
        """Type the given key into the current user line."""
        if key == "BSPC":
            self.current_line = self.current_line[:-1]
        elif key == "SPC":
            self.current_line += " "
        elif key == "UP" and self.prev_lines:
            self.prev_lines = [self.current_line] + self.prev_lines
            self.current_line = self.prev_lines.pop(-1)
        elif key == "DOWN" and self.prev_lines:
            self.prev_lines.append(self.current_line)
            self.current_line = self.prev_lines.pop(0)
        elif len(key) == 1:
            self.current_line += key


    def submit_line(self) -> str:
        """Print and return the current user line."""
        ln = self.current_line
        self.prev_lines.append(ln)
        if len(self.prev_lines) > _MAX_STORED_LINES:
            self.prev_lines.pop(0)
        self.print(f"\x1b[36m{os.getcwd()}$ \x1b[96m{ln}\x1b[0m")
        self.current_line = ""
        self.draw()
        self.display.show()
        return ln


    @staticmethod
    def _blink_state() -> bool:
        return (time.ticks_ms() % _CURSOR_BLINK_MOD) < _CURSOR_BLINK_MS

    def draw(self):
        """Draw all the terminal lines."""
        # Only draw all lines if we have to
        if self.lines_changed:
            self.display.fill(self.display.palette[2])
            y = _PRINT_LINE_START
            for line in self.lines:
                line.draw(0, y, self.display)
                y += 11

        # Draw current user line
        self._draw_user_text(f'{os.getcwd()}$ ', self.current_line)

    def _draw_user_text(self, cwd_line, user_line):
        # blackout user line
        self.display.rect(
            0, _USER_LINE_Y_FILL, _MH_DISPLAY_WIDTH, _USER_LINE_HEIGHT, self.display.palette[1], fill=True,
        )
        if len(user_line) + len(cwd_line) >= _MAX_TEXT_WIDTH:
            # text too long
            x = _MH_DISPLAY_WIDTH - (len(user_line) + len(cwd_line) + 1)*8
        else:
            x = 0
        self.display.text(cwd_line, x, _USER_LINE_Y, self.display.palette[5])
        x += len(cwd_line) * 8
        self.display.text(user_line, x, _USER_LINE_Y, self.display.palette[7])
        x += len(user_line) * 8
        self.display.text("_", x, _USER_LINE_Y, self.display.palette[4 if self._blink_state() else 6])

