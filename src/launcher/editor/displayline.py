"""An object for holding and drawing tokenized/styled lines of text."""


class DisplayLine:
    """Holds tokenized lines for display."""

    def __init__(self, text):
        """Tokenize and store the given text."""
        self.text = text
