"""Object class for loading/structuring a raw bitmap file for use with the Display driver."""
import os


class RawBitmap:
    """Open a raw bitmap file for use with the Display core."""

    # Cache data for a single bitmap (within a specified size)
    cached_file = None
    cache = None
    mv = None

    def __init__(self, file_path: str, width: int, height: int, palette: list[int, ...]):
        """Construct the bitmap from given file."""
        self.WIDTH = width
        self.HEIGHT = height
        self.PALETTE = palette
        # This assumes that the bits per pixel is always the minimum possible:
        self.BPP = self._find_bpp(len(palette))

        # The size of the file in bytes
        self.size = os.stat(file_path)[6]
        # Open the file for reading
        self.f = open(file_path, 'rb')  # noqa: SIM115
        self.deinit = self.f.close


    @staticmethod
    @micropython.viper
    def _find_bpp(count: int) -> int:
        """Find the minimum bits that can be used to encode count colors."""
        bpp = 1
        while (1 << bpp) < count:
            bpp += 1
        return bpp


    def __getattr__(self, key):
        """Cache the bitmap, and return the cache."""
        if key != "BITMAP":
            raise AttributeError(key)

        # Cache this bitmap:
        if RawBitmap.cached_file is not self.f:
            RawBitmap.cache = bytearray(self.size)
            self.f.seek(0)
            self.f.readinto(RawBitmap.cache)
            RawBitmap.mv = memoryview(RawBitmap.cache)

        return RawBitmap.mv
