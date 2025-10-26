# mh_include_if i2s_speaker:
"""Play audio by sending samples to an I2S peripheral."""
from machine import Pin, I2S
from .output import Output



class I2SOutput(Output):
    """Play audio using I2S."""

    def __init__(
            self,
            sck: int,
            ws: int,
            sd: int,
            channels: int = 4,
            rate: int = 11025,
            buf_size: int = 1024,
    ):
        """Initialize the I2S output."""
        self.i2s = I2S(
            1,
            sck=Pin(sck),
            ws=Pin(ws),
            sd=Pin(sd),
            mode=I2S.TX,
            bits=16,
            format=I2S.MONO,
            rate=rate,
            ibuf=max(buf_size, 1024),
        )
        self.buf = bytearray(buf_size)
        self.mv = memoryview(self.buf)
        super().__init__(channels=channels, rate=rate)
        self.i2s.irq(self._handle_write)
        self._handle_write(None)


    @staticmethod
    @micropython.viper
    def erase_buffer(buf):
        """Reset the given buffer to a neutral signal."""
        buf_len = int(len(buf)) // 2
        buf_ptr = ptr16(buf)
        i = 0
        while i < buf_len:
            buf_ptr[i] = 0
            i += 1


    def _handle_write(self, _):
        """IRQ for I2S; write held data and ready the next data to write."""
        self.i2s.write(self.mv)

        self.erase_buffer(self.mv)
        self.fill_buffer(self.mv)


    def deinit(self):
        """De-initialize the audio output."""
        self.i2s.deinit()
        super().deinit()
