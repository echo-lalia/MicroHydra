"""Lines class for the Terminal."""


txt_clrs = {
    '30': 0,
    '31': 55749,
    '32': 15785,
    '33': 65057,
    '34': 886,
    '35': 28974,
    '36': 11772,
    '37': 52825,
    '90': 33808,
    '91': 63488,
    '92': 2016,
    '93': 65504,
    '94': 31,
    '95': 63519,
    '96': 2047,
    '97': 65535,
}
# bg colors are txt colors + 10


class _StyleStr:
    """Color/style and string, for the Line class."""

    # class level style helps us remember styling between strings/lines
    text_color = None
    bg_color = None
    bold = False
    def __init__(self, text):
        if text.startswith('\033[') and 'm' in text:
            # Get style attributes
            text = text[2:]
            style, text = text.split('m', 1)


            for styl in style.split(';'):

                print(f'{styl=}')
                # Style resetters:
                if styl == '0':  # Reset all
                    _StyleStr.text_color = None
                    _StyleStr.bg_color = None
                    _StyleStr.bold = False
                elif styl == '39':  # Default foreground color
                    _StyleStr.text_color = None
                elif styl == '49':  # Default background color
                    _StyleStr.bg_color = None

                elif styl == '1':  # Bold
                    _StyleStr.bold = True

                # text color
                elif styl in txt_clrs:
                    _StyleStr.text_color = txt_clrs[styl]

                # BG color
                elif styl.isdigit() and str(int(styl) - 10) in txt_clrs:
                    _StyleStr.bg_color = txt_clrs[str(int(styl) - 10)]

        self.text = text
        self.txt_clr = _StyleStr.text_color
        self.bg_clr = _StyleStr.bg_color
        self.bold = _StyleStr.bold


class Line:
    """Single line, with color support."""

    def __init__(self, text):
        """Create a line with the given text."""
        self.strings = self._get_strings(text)

    @staticmethod
    def get_strings(string) -> list[_StyleStr]:
        """Get style strings from text."""
        strings = []
        current_str = ''
        while string:
            if string.startswith('\033[') \
            and current_str:
                strings.append(_StyleStr(current_str))
                current_str = ''
            current_str += string[0]
            string = string[1:]
        strings.append(_StyleStr(current_str))
        return strings
