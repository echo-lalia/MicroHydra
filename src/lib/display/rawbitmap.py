"""Object class for loading/structuring a raw bitmap file for use with the Display driver."""
import os


class RawBitmap:
    """Open a raw bitmap file for use with the Display core."""

    cached_path = None
    cache = None

    def __init__(self, file_path: str, width: int, height: int, palette: list[int, ...]):
        """Construct the bitmap from given file."""
        self.WIDTH = width
        self.HEIGHT = height
        self.PALETTE = palette

        # This assumes that the bits per pixel is always the minimum possible:
        self.BPP = 1
        while len(palette) > (1 << self.BPP):
            self.BPP += 1

        if RawBitmap.cached_path == file_path:
            # Use the cached buffer rather than reloading
            self.size = len(RawBitmap.cache)
            self.BITMAP = RawBitmap.cache
        else:
            # Load and cache a new buffer
            self.size = os.stat(file_path)[6]
            with open(file_path, 'rb') as f:
                buf = bytearray(self.size)
                f.readinto(buf)
                self.BITMAP = memoryview(buf)

            RawBitmap.cached_path = file_path
            RawBitmap.cache = self.BITMAP

    @classmethod
    def clean(cls):
        """Clear the bitmap cache."""
        cls.cached_path = None
        cls.cache = None
