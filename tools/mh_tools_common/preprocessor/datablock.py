"""Container for strings and MHConditionalBlocks."""
from mhcontrol import MHControl



class DataBlock:
    """Container to hold and handle file strings, and MHConditionalBlocks."""

    def __init__(self, data: list[str]):
        """Construct a data block using the given lines."""
        self.source_data = data
        self.data = self.load_data(data)


    @staticmethod
    def load_data(data: list[str]) -> list[str]:
        """Load string data into strings, and MHConditionalBlocks."""
