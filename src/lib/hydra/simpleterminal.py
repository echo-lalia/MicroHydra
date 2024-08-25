"""
This module provides a simple and lightweight scrolling terminal display.
It can be used to simply print status information to the device.

When `immediate` is set to `True` (the default value), it draws and shows itself every time you print to it.
When `False`, only draw when you call the draw method. You must call `Display.show` manually.
"""
from lib.display import Display
from lib.hydra.config import Config


_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)
_MAX_H_CHARS = const(_MH_DISPLAY_WIDTH // 8)
_MAX_V_LINES = const(_MH_DISPLAY_HEIGHT // 9)

class SimpleTerminal:
    lines = []
    immediate=True
    def __init__(self, immediate=True):
        if not hasattr(Display, 'instance'):
            raise AttributeError("Display has no instance. Please init 'Display' before 'SimpleTerminal'")
        self.display = Display.instance
        self.config = Config.instance if hasattr(Config, 'instance') else Config()
        self.immediate = immediate


    def print(self, text):
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
        for idx, line in enumerate(self.lines):
            self.display.text(
                line,
                0, idx * 9,
                self.config.palette[8 if idx == len(self.lines) - 1 else 7]
                )
