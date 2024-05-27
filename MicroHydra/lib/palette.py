"""
This Palette class is designed to be used for storing a list of RGB565 colors,
and for returning the apropriate colors by index to be used with MicroHydra's display module.

Key notes on Palette:
  - uses a bytearray to store color information,
    this is intended for fast/easy use with Viper's ptr16.

  - Returns an RGB565 color when using normal framebuffer, or an index of the color if use_tiny_buf.
    (This makes it so that you can pass a `Palette[i]` to the Display class in either mode.)
    
  - Palette is a singleton, which is important so that different MH classes can modify and share it's data
    (without initializing the Display).
"""

# Palette class
class Palette:
    use_tiny_buf = False
    buf = bytearray(32)
    def __new__(cls):
        if not hasattr(cls, 'instance'):
          cls.instance = super(Palette, cls).__new__(cls)
        return cls.instance


    def __len__(self) -> int:
        return len(self.buf) // 2


    @micropython.viper
    def __setitem__(self, key:int, new_val:int):
        buf_ptr = ptr16(self.buf)
        buf_ptr[key] = new_val


    @micropython.viper
    def __getitem__(self, key:int) -> int:
        # if using tiny buf, the color should be the index for the color
        if self.use_tiny_buf:
            return key

        buf_ptr = ptr16(self.buf)
        return buf_ptr[key]
    
    
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]


if __name__ == '__main__':
    palette = Palette()
    print(palette == Palette())
    palette.use_tiny_buf = False
    print(palette.use_tiny_buf)
    print(palette == Palette())
    print(palette.use_tiny_buf)
    