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
            with open(file_path, 'rb') as f:
                buf = bytearray(self.size)
                f.readinto(buf)
            if file_path.endswith('.wbmp'):
                self.wbmp2bitmap(buf)
            else:
                self.BITMAP = memoryview(buf)
                self.WIDTH = 32
                self.HEIGHT = 32

            RawBitmap.cached_path = file_path
            RawBitmap.cache = self.BITMAP
            RawBitmap.cached_w = self.WIDTH
            RawBitmap.cached_h = self.HEIGHT
    
    def wbmp2bitmap(self, buf):
        idx = 2
        self.WIDTH, idx = self.read_mbi(buf, idx)
        self.HEIGHT, idx = self.read_mbi(buf, idx)
        self.BITMAP = memoryview(buf[idx:])
        
    @staticmethod
    def read_mbi(data, index):
        """Reads multi-byte integer starting at index."""
        value = 0
        while True:
            byte = data[index]
            index += 1
            value = (value << 7) | (byte & 0x7F)
            if not (byte & 0x80):  # if high bit is 0, stop reading
                break
        return value, index

    @classmethod
    def clean(cls):
        """Clear the bitmap cache."""
        cls.cached_path = None
        cls.cached_w = None
        cls.cached_h = None
        cls.cache = None

