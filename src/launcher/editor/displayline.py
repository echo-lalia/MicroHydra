"""An object for holding and drawing tokenized/styled lines of text."""


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Constants: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

_FONT_HEIGHT = const(8)
_FONT_WIDTH = const(8)

_LINE_PADDING = const(2)
_FULL_LINE_HEIGHT = const(_LINE_PADDING + _FONT_HEIGHT)
_LINE_BG_HEIGHT = const(_FULL_LINE_HEIGHT - 1)


class DisplayLine:
    """Holds tokenized lines for display."""

    tokenizer = None

    def __init__(self, text):
        """Tokenize and store the given text."""
        self.tokens = DisplayLine.tokenizer.tokenize(text)


    def draw(self, display, x, y):
        """Draw all the tokens in this line."""
        # Blackout line
        display.rect(0, y, _MH_DISPLAY_WIDTH, _LINE_BG_HEIGHT, display.palette[2], fill=True)

        # Draw each token
        for token in self.tokens:
            print(repr(token.text))
            display.text(token.text, x, y, display.palette[token.color])
            x += len(token.text) * _FONT_WIDTH
