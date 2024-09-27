"""Terminal class to write and display to."""
from lib.display import Display
from launcher.terminal.termline import TermLine
from lib.hydra.utils import get_instance
import os

_MH_DISPLAY_WIDTH = const(240)
_MH_DISPLAY_HEIGHT = const(135)

_NUM_PRINT_LINES = const(_MH_DISPLAY_HEIGHT // 10)
_PRINT_LINE_START = const(_MH_DISPLAY_HEIGHT - 12 - (_NUM_PRINT_LINES * 10))
_MAX_TEXT_WIDTH = const(_MH_DISPLAY_WIDTH // 8)

class Terminal:
    """Graphical terminal, for printing to."""

    def __init__(self):
        """Create the terminal."""
        self.lines = [TermLine('')] * _NUM_PRINT_LINES
        self.display = get_instance(Display)

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

    def draw(self):
        """Draw all  the terminal lines."""
        y = _PRINT_LINE_START
        for line in self.lines:
            line.draw(0, y, self.display)
            y += 10


if __name__ == '__main__':
    # JUST FOR TESTING
    from lib.hydra.config import Config
    config = Config()
    display = Display()

    term = Terminal()

    term.print('HELLO, WORLD!!!')
    term.print('\x1b[6;30;42m' + 'Success!' + '\x1b[0m')
    term.print('The quick brown fox jumped over the lazy dog. Also this is some additional text! ertyuhlgfhdseryu5thlkjvmgcfdhrtutiylhkb,vmcngfdtyuiçjl,hvg')
    term.print('!@#$%*() ´`~^°w?ç§ºª')
    term.draw()
    display.show()


