"""DisplayLine holds pre-styled tokens for fast redrawing of text."""
if __name__ == '__main__': from launcher import editor  # relative import for testing


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

_UNDERLINE_PADDING_L = const(_LEFT_MARGIN)
_UNDERLINE_PADDING_R = const(18)
_UNDERLINE_WIDTH = const(_MH_DISPLAY_WIDTH - _UNDERLINE_PADDING_L - _UNDERLINE_PADDING_R)


# rare whitespace char is repurposed here to denote converted tab/space indents
_INDENT_SYM = const(' ')  # noqa: RUF001



class DisplayLine:
    """Holds tokenized lines for display."""

    tokenizer = None

    def __init__(self, text: str):
        """Tokenize and store the given text."""
        self.tokens = DisplayLine.tokenizer.tokenize(text)
        # Store indentation x-offsets for quick drawing
        self.indents = self._get_indents(text)


    @staticmethod
    def _get_indents(text: str) -> list[int]:
        return [idx * _FONT_WIDTH + _LEFT_MARGIN for idx, char in enumerate(text) if char == _INDENT_SYM]


    def draw(self, display, x:int, y:int, *, selected: bool = False):
        """Draw all the tokens in this line."""
        # Blackout line
        if selected:
            display.rect(0, y, _MH_DISPLAY_WIDTH, _FULL_LINE_HEIGHT, display.palette[1], fill=True)
        else:
            display.rect(0, y, _MH_DISPLAY_WIDTH, _FULL_LINE_HEIGHT, display.palette[2], fill=True)
#             display.hline(_UNDERLINE_PADDING_L, y+_LINE_BG_HEIGHT, _UNDERLINE_WIDTH, display.palette[1])


        # Draw indentation
        for x_offset in self.indents:
            display.vline(
                x_offset + x,
                y,
                _FULL_LINE_HEIGHT,
                display.palette[3 if selected else 0],
            )


        y += _LINE_TEXT_OFFSET
        x += _LEFT_PADDING

        # Draw each token
        for token in self.tokens:
            display.text(token.text, x, y, token.color)
            x += len(token.text) * _FONT_WIDTH
