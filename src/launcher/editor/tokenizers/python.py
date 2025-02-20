"""A code tokenizer that highlights Python syntax."""
from .common import *
from lib.hydra.color import mix_color565



_FONT_WIDTH = const(8)



# arbitrary char classifications as int (used for syntax highlighting):
_NONE_CLASS = const(0)        # ""
_QUOTE_CLASS = const(5)       # "'", '"'
_UNDERSCORE_CLASS = const(6)  # "_"
_ALPHA_CLASS = const(7)       # A-Z and a-z
_DIGIT_CLASS = const(8)       # 0-9
_DOT_CLASS = const(9)         # "."
_SPACE_CLASS = const(1)       # Whitespace chars
_INDENT_CLASS = const(2)      # Special indent placeholder char
_OTHER_CLASS = const(4)       # All other symbols




_KEYWORDS = {
    'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif',
    'else', 'except', 'False', 'finally', 'for', 'from', 'global', 'if',
    'import', 'in', 'is', 'lambda', 'None', 'nonlocal', 'not', 'or', 'pass',
    'raise', 'return', 'True', 'try', 'while', 'with', 'yield',
    'int', 'float', 'str', 'dict', 'tuple', 'bytes', 'bytearray',
    'complex', 'list', 'set', 'const', 'type',
}


COLORS = {}


# These sets are required multiple times in this code, so I'm reusing them rather than recreating them each time.
DOT_UNDERSCORE_SET = {".", "_"}
QUOTE_SET = {"'", '"', '"""', "'''"}


def init(config):
    """Initialize tokenizer."""
    COLORS["default"] = config.palette[8]
    COLORS["comment"] = config.palette[5]
    COLORS["num"] = config.palette[14]
    COLORS["keyword"] = config.palette[15]

    COLORS["symbol"] = mix_color565(
        config.palette[15],
        config.palette[8],
        0.5,
        sat_mix_fac=0.2,
    )

    COLORS["string"] = mix_color565(
        config.palette[14],
        config.palette[8],
        0.3,
        sat_mix_fac=0.2,
    )


@micropython.viper
def classify_char(ch) -> int:
    """Classify char types for comparison. Returns an int representing the type."""
    if not ch:
        return _NONE_CLASS

    char = int(ord(ch))

    # These integers are chosen based on codepoint groupings from `ord`
    if char < 33:
        return _SPACE_CLASS

    if 97 <= char <= 122 \
    or 65 <= char <= 90:
        return _ALPHA_CLASS

    if char == 95:
        return _UNDERSCORE_CLASS

    if 48 <= char <= 57:
        return _DIGIT_CLASS

    if char == 46:
        return _DOT_CLASS

    if char == 8201:  # codepoint for editors indent symbol
        return _INDENT_CLASS

    if char == 39 or char == 34:  # noqa: PLR1714
        return _QUOTE_CLASS

    return _OTHER_CLASS


def is_var(string) -> bool:
    """Check if string could be a variable name."""
    for idx, char in enumerate(string):
        if idx == 0:
            # first char can only be underscore or letter
            if not (char.isalpha() or char == "_"):
                return False
        # chars must be alphanumeric or underscores
        elif not (char.isalpha() or char == "_" or char.isdigit()):
            return False
    return True


def is_numeric(string) -> bool:
    """Check if string is numeric. (With support for '_' and '.')."""
    any_numbers = False
    for char in string:
        if char.isdigit():
            any_numbers = True
        elif char not in DOT_UNDERSCORE_SET:
            return False
    return any_numbers


def split_line_segments(line:str):  # noqa: PLR0912, PLR0915
    """Yield token segments from line."""
    # Track current segment
    segment = ""
    segment_class = None
    prev_class = None

    # Are we currently in quotes? And what type of quotes?
    current_quote_type = None


    # We are iterating using the index so that we can jump forward when needed
    idx = 0
    while idx < len(line):
        char = line[idx]
        char_class = classify_char(char)


        ##### Special logic for quotes, overriding all other styling
        if char_class == _QUOTE_CLASS:
            # Check if the next 3 chars are all the same quote char
            # and store the current quote (Either the next 3 chars, or just the current one)
            next_3 = line[idx: idx+3]
            this_quote = next_3 if len(next_3) == 3 and all(ch == char for ch in next_3) else char

            if current_quote_type is None:
                # We aren't in quotes currently, so we should start a new quote segment.
                # Return the previous segment if it exists
                if segment:
                    yield segment
                segment_class = _QUOTE_CLASS
                segment = this_quote
                current_quote_type = this_quote
                # If we just added a triple-quote, we don't need to go over these chars again.
                if len(this_quote) == 3:
                    idx += 2

            elif this_quote == current_quote_type:
                # Our quotes match the start quotes. We should add them and end the segment.
                segment += this_quote
                yield segment
                segment = ""
                segment_class = None
                current_quote_type = None
                # If we just added a triple-quote, we don't need to go over these chars again.
                if len(this_quote) == 3:
                    idx += 2
            else:
                # Otherwise, this is the wrong quote type to end the string. So, just add the char normally.
                segment += char

        elif current_quote_type:
            # If we are in a string, all char types can be added to the segment.
            segment += char


        ##### The start of a comment:
        elif char == "#":
            # If we aren't in a string, a "#" indicates the start of a comment.
            # The whole rest of the line can be added to this segment, and we can stop scanning.
            if segment:
                yield segment
            segment = line[idx:]
            break


        ##### Any new symbol after a space should create a new segment:
        elif prev_class == _SPACE_CLASS and char_class != _SPACE_CLASS:
            yield segment
            segment = char
            segment_class = char_class


        ##### Matching char class:
        elif segment_class == char_class or char_class == _SPACE_CLASS:  # noqa: PLR1714
            # If the new char is the same class as the start char,
            # OR it's a trailing space,
            # we can add the char to the current segment.
            segment += char


        ##### Special logic allowing underscores and numbers in variables:
        elif segment_class == _UNDERSCORE_CLASS and char_class in {_ALPHA_CLASS, _DIGIT_CLASS}:
            # If we started with an underscore and now have a letter or number,
            # we can add it to the segment, and reclassify it as an _ALPHA_CLASS segment
            segment += char
            segment_class = _ALPHA_CLASS

        elif segment_class == _ALPHA_CLASS and char_class in {_DIGIT_CLASS, _UNDERSCORE_CLASS}:
            # Underscores and numbers can be added to variable names, so combine these into one segment.
            segment += char


        ##### Special logic to allow dots and underscores in numbers:
        elif segment_class == _DOT_CLASS and char_class == _DIGIT_CLASS:
            # Allow floats starting with a dot
            segment += char
            segment_class = _DIGIT_CLASS

        elif segment_class == _DIGIT_CLASS and char in DOT_UNDERSCORE_SET:
            # Dots and underscores are allowed in numbers
            segment += char


        ##### Char class doesn't match:
        else:
            # Otherwise, start a new segment.
            if segment:
                yield segment
            segment = char
            segment_class = char_class


        # Remember previous character
        prev_class = char_class
        # Iterate index
        idx += 1

    # Finally, yield the remaining segment
    if segment:
        yield segment



def style_token(segment: str):
    """Generate token color and BG color for a given segment."""
    if not segment:
        return COLORS['default'], None

    if segment.startswith("#"):
        return COLORS['comment'], None

    start_class = classify_char(segment[0])

    if start_class == _QUOTE_CLASS:
        return COLORS['string'], None

    if start_class in {_UNDERSCORE_CLASS, _ALPHA_CLASS}:
        # Check for builtins/keywords
        if segment.strip() in _KEYWORDS:
            return COLORS['keyword'], None
        return COLORS['default'], None

    if segment == ".":
        return COLORS['symbol'], None

    if all(ch.isdigit() or ch in {" ", "_", "."} for ch in segment):
        return COLORS['num'], None

    if start_class == _OTHER_CLASS:
        return COLORS['symbol'], None

    # Default/unstyled
    return COLORS['default'], None




def tokenize(line: str) -> tuple[int, str]:
    """Split/style text into a list of styled tokens."""
    tokens = []
    for segment in split_line_segments(line):
        clr, bg = style_token(segment)
        tokens.append(token(segment, clr, bg))

    return tokens
