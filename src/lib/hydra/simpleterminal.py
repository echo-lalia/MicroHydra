"""A simple (graphical) terminal.

This module provides a simple and lightweight scrolling terminal display.
It can be used to simply print status information to the device.

When `immediate` is set to `True` (the default value), it draws and shows itself every time you print to it.
When `False`, only draw when you call the draw method. You must call `Display.show` manually.
"""

from lib.display import Display
from .config import Config
from .utils import get_instance


_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)
_MAX_H_CHARS = const(_MH_DISPLAY_WIDTH // 8)
_MAX_V_LINES = const(_MH_DISPLAY_HEIGHT // 9)

class SimpleTerminal:
    """A simple scrolling terminal view."""

    lines = []
    immediate=True
    def __init__(self, *, immediate: bool = True):
        """Create the SimpleTerminal.

        If immediate == True, updates to the terminal are instantly drawn to the display.
        (Otherwise you must manually call `SimpleTerminal.draw` and `Display.show`)
        """
        self.display = get_instance(Display)
        self.config = get_instance(Config)
        self.immediate = immediate


    def print(self, text: str):  # noqa: D102
        text = str(text)
        print(text)

        new_lines = []

        # cut up line when it's too long
        while len(text) > _MAX_H_CHARS:
            new_lines.append(text[:_MAX_H_CHARS])
            text = text[_MAX_H_CHARS:]
        new_lines.append(text)

        # add new lines, trim to correct length
        self.lines += new_lines
        if len(self.lines) > _MAX_V_LINES:
            self.lines = self.lines[-_MAX_V_LINES:]

        if self.immediate:
            self.display.fill(self.config.palette[2])
            self.draw()
            self.display.show()


    def draw(self):
        """Draw the terminal to the display."""
        for idx, line in enumerate(self.lines):
            self.display.text(
                line,
                0, idx * 9,
                self.config.palette[8 if idx == len(self.lines) - 1 else 7]
                )
