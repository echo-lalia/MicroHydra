"""Object class for loading/structuring a WBMP bitmap file for use with the Display driver."""

class WBMPBitmap:
    """Open WBMP bitmap file for use with the Display core."""

    cached_path = None
    cached_w = None
    cached_h = None
    cache = None

    def __init__(self, file_path: str, palette: list[int, ...]):
        """Construct the bitmap from given WBMP file."""
        self.PALETTE = palette

        # WBMP always uses 1 bit per pixel
        self.BPP = 1
        self.BYTE_ALIGN = True

        if WBMPBitmap.cached_path == file_path:
            # Use the cached buffer rather than reloading
            self.size = len(WBMPBitmap.cache)
            self.BITMAP = WBMPBitmap.cache
            self.WIDTH = WBMPBitmap.cached_w
            self.HEIGHT = WBMPBitmap.cached_h
        else:
            with open(file_path, 'rb') as f:
                f.read(2)    # first 2 bytes are always 0
                self.WIDTH = self.read_mbi(f)
                self.HEIGHT = self.read_mbi(f)
                raw = (f.read())
            buf = self._wbmp_dealign(raw, self.WIDTH, self.HEIGHT)
            self.size = len(buf)
            self.BITMAP = memoryview(buf)
                
            WBMPBitmap.cached_path = file_path
            WBMPBitmap.cache = self.BITMAP
            WBMPBitmap.cached_w = self.WIDTH
            WBMPBitmap.cached_h = self.HEIGHT
        
    @staticmethod
    def read_mbi(f):
        """Reads a multi-byte integer from a file starting at a specific byte."""
        value = 0
        while True:
            byte = f.read(1)
            if not byte:
                raise EOFError("Unexpected EOF while reading WBMP header.")
            b = byte[0]
            value = (value << 7) | (b & 0x7F)
            if not (b & 0x80):  # 0 in first bit means last byte
                break
        
        return value
    
    @staticmethod
    def _wbmp_dealign(buf, width, height):
        src_stride = (width + 7) >> 3
        total_bits = width * height
        dst_len = (total_bits + 7) >> 3
        dst = bytearray(dst_len)

        dst_bit = 0
        for y in range(height):
            row_base = y * src_stride
            for x in range(width):
                src_byte = buf[row_base + (x >> 3)]
                bit = (src_byte >> (7 - (x & 7))) & 1

                if bit:
                    dst[dst_bit >> 3] |= 1 << (7 - (dst_bit & 7))
                dst_bit += 1

        return dst

    @classmethod
    def clean(cls):
        """Clear the bitmap cache."""
        cls.cached_path = None
        cls.cached_w = None
        cls.cached_h = None
        cls.cache = None
