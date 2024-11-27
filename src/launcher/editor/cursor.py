"""A simple contianer to hold the user's cursor."""

class Cursor:
    """The user's cursor."""

    def __init__(self):
        """Create a new cursor at 0,0."""
        self.x = 0
        self.y = 0

    def clamp_to_text(self, filelines):
        """Clamp cursor to file text."""
