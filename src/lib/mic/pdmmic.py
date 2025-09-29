"""Simple PDM mic support."""

from machine import Pin, I2S
import time


_SAMPLE_SIZE = const(16)

_DEFAULT_BUFFER_LEN = const(8192 // 2)
_DEFAULT_SAMPLE_RATE = const(11025)

class PDMMic:
    """Simple class to read values from a PDM mic.

    MicroPython does not currently have official PDM mic support for the ESP32,
    so this class is treating the mic like an I2S input,
    and adding all the bits together to make samples from 0-255.
    """

    def __init__(
            self,
            _id,
            *,
            sck,
            ws,
            sd,
            buffer_length=_DEFAULT_BUFFER_LEN,
            rate=_DEFAULT_SAMPLE_RATE):
        """Init the microphone."""
        self.pdm = I2S(
            _id,
            sck=sck,
            ws=ws,
            sd=sd,
            mode=I2S.RX,
            bits=_SAMPLE_SIZE,
            format=I2S.MONO,
            rate=rate,
            ibuf=buffer_length,
        )
        self.buf = bytearray(_SAMPLE_SIZE)

    @micropython.viper
    def amplitude(self) -> int:
        """Get the difference between min/max samples."""
        _AMPLITUDE_SAMPLES = const(8)
        minimum = 255
        maximum = 0
        i = 0
        while i < _AMPLITUDE_SAMPLES:
            sample = int(self.sample())
            if sample < minimum:
                minimum = sample
            if sample > maximum:
                maximum = sample
            i += 1
        return maximum - minimum

    @micropython.viper
    def sample(self) -> int:
        """Get a single sample from the mic."""
        self.pdm.readinto(self.buf)
        buf = ptr8(self.buf)

        sample = 0
        # Iterate through each byte in the sample buffer
        idx = 0
        while idx < _SAMPLE_SIZE:
            byte = buf[idx]
            # iterate over each bit in the byte
            bit_idx = 0
            while bit_idx < 8:
                sample += (byte >> bit_idx) & 1
                bit_idx += 1
            idx += 1
        return sample

    @micropython.viper
    def readinto(self, buffer):
        """Fill the given buffer with samples."""
        # This is the bit used to mark a negative number
        _TWOS_COMPLIMENT_SIGN = const(0b1000_0000_0000_0000)

        # start by reading raw data into the buffer
        self.pdm.readinto(buffer)

        # Convert raw PDM data (lazily) into 16-bit samples
        buf_len = int(len(buffer)) // 2  # 16 bit len
        buf_ptr = ptr16(buffer)
        buf_idx = 0
        while buf_idx < buf_len:
            raw_sample = buf_ptr[buf_idx]
            sample = 0
            # iterate over each bit in the sample
            bit_idx = 0
            while bit_idx < 16:
                sample += (raw_sample >> bit_idx) & 1
                bit_idx += 1

            # lazily scale int (0-15) into 16 bit (0-65535)
            # (Also, convert into positive/negative with twos compliment)
            sample *= 4369
            buf_ptr[buf_idx] = (
                sample - _TWOS_COMPLIMENT_SIGN if sample > _TWOS_COMPLIMENT_SIGN
                else (sample-_TWOS_COMPLIMENT_SIGN) | _TWOS_COMPLIMENT_SIGN
            )
            buf_idx += 1


if __name__ == "__main__":

#     # test by reading data into a buffer and playing it over speaker
#     # results are not great... but it DOES work.
#     SCK_PIN = 43
#     WS_PIN = 41
#     SD_PIN = 46
#     I2S_ID = 0
#
#     mic = PDMMic(
#         I2S_ID,
#         sck=Pin(SCK_PIN),
#         ws=Pin(WS_PIN),
#         sd=Pin(SD_PIN),
#         rate=_DEFAULT_SAMPLE_RATE*2,
#     )
#
#     audio_buf = bytearray(70000)
#     print("Listening...")
#     mic.readinto(audio_buf)
#     print("Playing back...")
#     from lib.audio import Audio
#     audio = Audio(rate=_DEFAULT_SAMPLE_RATE*2)
#     audio.play(audio_buf, volume=10, loop=True)
#     time.sleep(10)
#     audio.stop()


    # Testing the class by drawing a linegraph to the display
    from lib.display import Display

    display = Display()
    prev_y = display.height
    px_x = display.width - 2
    
    SCK_PIN = 43
    WS_PIN = 41
    SD_PIN = 46
    I2S_ID = 0

    mic = PDMMic(
        I2S_ID,
        sck=Pin(SCK_PIN),
        ws=Pin(WS_PIN),
        sd=Pin(SD_PIN),
    )

    while True:
        sample = mic.sample()
        line_y = display.height - (sample * display.height) // 256

        display.scroll(-1,0)
        display.line(
            px_x - 1, prev_y,
            px_x, line_y,
            65535,
        )
        display.show()
        prev_y = line_y
