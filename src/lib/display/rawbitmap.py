"""Object class for loading/structuring a bitmap file for use with the Display driver."""
import os


class RawBitmap:
    """Open a raw bitmap file for use with the Display core."""

    cached_path = None
    cached_w = None
    cached_h = None
    cache = None

    def __init__(self, file_path: str, palette: list[int, ...]):
        """Construct the bitmap from given file."""
        self.PALETTE = palette

        # This assumes that the bits per pixel is always the minimum possible:
        self.BPP = 1
        while len(palette) > (1 << self.BPP):
            self.BPP += 1

        if RawBitmap.cached_path == file_path:
            # Use the cached buffer rather than reloading
            self.size = len(RawBitmap.cache)
            self.BITMAP = RawBitmap.cache
            self.WIDTH = RawBitmap.cached_w
            self.HEIGHT = RawBitmap.cached_h
        else:
            # Load and cache a new buffer
            self.size = os.stat(file_path)[6]
            if file_path.endswith(".wbmp"):
                self.load_wbmp(file_path)
            else:
                self.load_raw(file_path)

            RawBitmap.cached_path = file_path
            RawBitmap.cache = self.BITMAP
            RawBitmap.cached_w = self.WIDTH
            RawBitmap.cached_h = self.HEIGHT

    def load_raw(self, file_path: str):
        with open(file_path, 'rb') as f:
            buf = bytearray(self.size)
            f.readinto(buf)
            self.BITMAP = memoryview(buf)
            self.WIDTH = 32
            self.HEIGHT = 32

    def load_wbmp(self, file_path: str):
        with open(file_path, 'rb') as f:
            buf = bytearray(self.size)
            f.readinto(buf)
            self.BITMAP = memoryview(buf)[4:]
            self.WIDTH = memoryview(buf)[2]
            self.HEIGHT = memoryview(buf)[3]

    @classmethod
    def clean(cls):
        """Clear the bitmap cache."""
        cls.cached_path = None
        cls.cached_w = None
        cls.cached_h = None
        cls.cache = None
