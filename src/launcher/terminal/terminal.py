"""Terminal class to write and display to."""
from lib.display import Display
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


class Terminal:
    """Graphical terminal, for printing to."""

    def __init__(self):
        """Create the terminal."""
        self.lines = [TermLine('')] * _NUM_PRINT_LINES
        self.current_line = ''
        self.display = get_instance(Display, allow_init=False)
        self.lines_changed = False

    @staticmethod
    def split_lines(text:str, max_length:int=_MAX_TEXT_WIDTH) -> list[str]:
        """Split a string into multiple lines, based on max line-length."""
        lines = []
        current_line = ''
        words = text.split()

        for word in words:
            while len(word) >= max_length:
                lines.append(current_line)
                current_line = word[:max_length]
                word = word[max_length:]
            if len(word) + len(current_line) >= max_length:
                lines.append(current_line)
                current_line = word
            elif len(current_line) == 0:
                current_line += word
            else:
                current_line += ' ' + word

        lines.append(current_line) # add final line

        return lines

    def print(self, *args, **kwargs):  # noqa: ARG002
        """Print to the terminal. Intended to be compatible with the `print` built-in.

        Currently does not support `print` kwargs.
        """
        text = ' '.join(args)
        lines = self.split_lines(text)
        for line in lines:
            self.lines.append(TermLine(line))
            self.lines.pop(0)
        self.lines_changed = True

    @staticmethod
    def _blink_state() -> bool:
        return (time.ticks_ms() % _CURSOR_BLINK_MOD) < _CURSOR_BLINK_MS

    def draw(self):
        """Draw all  the terminal lines."""
        # Only draw all lines if we have to
        if self.lines_changed:
            self.display.fill(self.display.palette[2])
            y = _PRINT_LINE_START
            for line in self.lines:
                line.draw(0, y, self.display)
                y += 11

        # blackout user line
        self.display.rect(
            0, _USER_LINE_Y_FILL, _MH_DISPLAY_WIDTH, _USER_LINE_HEIGHT, self.display.palette[1], fill=True,
        )
        # Draw current user line
        x = 0
        cwd_line = f'{os.getcwd()}$'
        self.display.text(cwd_line, x, _USER_LINE_Y, self.display.palette[5])
        x += len(cwd_line) * 8
        self.display.text(self.current_line, x, _USER_LINE_Y, self.display.palette[8])
        x += len(self.current_line) * 8
        self.display.text("_", x, _USER_LINE_Y, self.display.palette[4 if self._blink_state() else 6])


if __name__ == '__main__':
    # JUST FOR TESTING
    from lib.hydra.config import Config
    config = Config()
    display = Display()

    term = Terminal()

    term.print("\x1b[34mTESTING some text in the terminal! \x1b[4mWOWIE!\x1b[0m")
    term.print('HELLO, WORLD!!!')
    term.print('\x1b[96mこんにちは世界！\x1b[0m')
    term.print('\x1b[95m你好世界！\x1b[0m')
    term.print('\x1b[31m' + 'FAILURE' + '\x1b[0m')
    term.print('\x1b[6;30;42m' + 'Success!' + '\x1b[0m')
    term.print('The quick brown fox jumped over the lazy dog. Also this is some additional text!')
    term.print('!@#$%*() ´`~^°w?ç§ºª')

    while True:
        term.draw()
        display.show()
        time.sleep_ms(10)
