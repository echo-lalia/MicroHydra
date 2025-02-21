"""A plain tokenizer that simply returns all text as a default token."""
from .common import *



_FONT_WIDTH = const(8)


COLORS = {}


def init(config):
    """Initialize tokenizer."""
    COLORS['default'] = config.palette[8]


def tokenize(line: str) -> tuple[int, str]:
    """Split/style text into a list of styled tokens."""
    return [token(line, COLORS['default'])]
