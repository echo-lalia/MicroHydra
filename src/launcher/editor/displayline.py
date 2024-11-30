"""An object for holding and drawing tokenized/styled lines of text."""


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

_FONT_HEIGHT = const(8)
_FONT_WIDTH = const(8)

_LINE_PADDING = const(2)
_FULL_LINE_HEIGHT = const(_LINE_PADDING + _FONT_HEIGHT)
_LINE_BG_HEIGHT = const(_FULL_LINE_HEIGHT - 1)
_LINE_TEXT_OFFSET = const(_LINE_PADDING // 2)


_LEFT_PADDING = const(4)
_LEFT_MARGIN = const(_LEFT_PADDING - 2)

_UNDERLINE_PADDING_L = const(4)
_UNDERLINE_PADDING_R = const(8)
_UNDERLINE_WIDTH = const(_MH_DISPLAY_WIDTH - _UNDERLINE_PADDING_L - _UNDERLINE_PADDING_R)

class DisplayLine:
    """Holds tokenized lines for display."""

    tokenizer = None

    def __init__(self, text):
        """Tokenize and store the given text."""
        self.tokens = DisplayLine.tokenizer.tokenize(text)


    def draw(self, display, x, y, selected=False):
        """Draw all the tokens in this line."""
        # Blackout line
        if selected:
            display.rect(0, y, _MH_DISPLAY_WIDTH, _FULL_LINE_HEIGHT, display.palette[1], fill=True)
            if x == 0: # Draw left margin
                display.vline(_LEFT_MARGIN, y, _FULL_LINE_HEIGHT, display.palette[2])
        else:
            display.rect(0, y, _MH_DISPLAY_WIDTH, _FULL_LINE_HEIGHT, display.palette[2], fill=True)
            display.hline(_UNDERLINE_PADDING_L, y+_LINE_BG_HEIGHT, _UNDERLINE_WIDTH, display.palette[1])
            if x == 0: # Draw left margin
                display.vline(_LEFT_MARGIN, y, _FULL_LINE_HEIGHT, display.palette[1])

        y += _LINE_TEXT_OFFSET
        x += _LEFT_PADDING
        # Draw each token
        for token in self.tokens:
            display.text(token.text, x, y, display.palette[token.color])
            x += len(token.text) * _FONT_WIDTH
