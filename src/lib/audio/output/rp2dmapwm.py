# mh_include_if rp2 and pwm_speaker:
"""Play PWM audio by using DMA to write samples to the RP2040's PWM register.

This module was written for the PicoCalc, with a Raspberry Pi Pico.
However, I would like to add support the Pico2 / RP2350 as well.
(and I hope it can work with devices other than the PicoCalc, too)

The RP2040 has 8 PWM slices, each with 2 channels (each slice has 2 separate 16bit counter and compare values).
For speed and simplicity (and possibly necessity) this module writes to *both* channels using a single 32-bit word.
This simplifies stereo playback, but it's also important because the DMA peripheral seems to
always write a 32-bit word (duplicating 8 or 16bit words to fit the space).


"""
from machine import Pin, PWM, mem32, freq
from rp2 import DMA
from .output import Output



# Reference: pg 108 of rp2040 datasheet.
_DMA_MEM_START = const(0x50000000)
# Memory offsets for DMA pacing timers
_DMA_MEM_TIM0 = const(_DMA_MEM_START + 0x420)
_DMA_MEM_TIM1 = const(_DMA_MEM_START + 0x424)
_DMA_MEM_TIM2 = const(_DMA_MEM_START + 0x428)
_DMA_MEM_TIM3 = const(_DMA_MEM_START + 0x42c)
# Flags for the DMA constructor to use a pacing timer for timing
_DMA_FLAG_TIM0 = const(0x3b)
_DMA_FLAG_TIM1 = const(0x3c)
_DMA_FLAG_TIM2 = const(0x3d)
_DMA_FLAG_TIM3 = const(0x3e)


@micropython.viper
def pin_2_pwm_slice(pin: int) -> int:
    """Calculate the PWM slice for a given rp2040 pin."""
    # mh_if rp2 and armv6m:
    # Reference: pg 522 of rp2040 datasheet.
    return pin % 16 // 2
    # mh_end_if


@micropython.viper
def mem_start_for_pwm_slice(slc: int) -> int:
    """Calculate the memory offset for a given pwm slice."""
    # mh_if rp2 and armv6m:
    # Reference: pg 530 of rp2040 datasheet.
    _PWM_MEM_START = const(0x40050000)
    return int(_PWM_MEM_START) | (0x14 * slc)
    # mh_end_if


@micropython.viper
def mem_addr_compare_for_pwm_slice(slc: int) -> int:
    """Calculate the memory offset for a given pwm slice's counter compare value."""
    # mh_if rp2 and armv6m:
    # Reference: pg 530 of rp2040 datasheet.
    return int(mem_start_for_pwm_slice(slc)) + 0x0c
    # mh_end_if


@micropython.viper
def mem_addr_top_for_pwm_slice(slc: int) -> int:
    """Calculate the memory offset for a given pwm slice's wrap value."""
    # mh_if rp2 and armv6m:
    # Reference: pg 530 of rp2040 datasheet.
    return int(mem_start_for_pwm_slice(slc)) + 0x10
    # mh_end_if


@micropython.viper
def timer_fraction_for_rate(rate: int) -> int:
    """Get a X/Y fraction for a pacing timer to match the given rate.

    Returns pre-calculated fractions for common sample rates,
    otherwise returns a close fraction of 65535.
    """
    # timer rate is tied to CPU frequency
    cpu_freq = int(freq())
    if cpu_freq == 200_000_000:
        # Try a pre-calculated value
        if rate == 8_000:
            return (1 << 16) | 25000
        if rate == 11_025:
            return (3 << 16) | 54422
        if rate == 16_000:
            return (1 << 16) | 12500
        if rate == 22_050:
            return (7 << 16) | 63492
        if rate == 44_100:
            return (7 << 16) | 31746
    # Fallback to calculating a fraction over 65535
    numerator = rate * 65535 // cpu_freq
    return (numerator << 16) | 65535




class Rp2DmaPwmOutput(Output):
    """Play audio to the RP2's PWM using DMA."""

    def __init__(
            self,
            pin: int,
            pin2: int|None = None,
            channels: int = 4,
            rate: int = 11025,
            buf_size: int = 1024,
    ):
        """Initialize the Rp2DmaPwm object.

        pin:
            The number of the GPIO pin to write to.
            This pin is initialized for PWM output, and it determines the PWM slice we write to with the DMA.
        pin2:
            An optional second pin to initialize for PWM output.
            This pin will only play audio if it's on the same PWM slice as `pin`.
        channels:
            the number of concurrent audio channels to allow.
        rate:
            The sample rate to use for output (should usually match the sample rate of the source).
        """
        # Double-buffer the audio so we can write one while the other plays
        self._bufs = [bytearray(buf_size), bytearray(buf_size)]
        self.mvs = [memoryview(self._bufs[0]), memoryview(self._bufs[1])]
        self.buf_size = buf_size

        # Initialize PWM for given pin(s)
        self.pwms = [PWM(Pin(pin))]
        if pin2 is not None:
            self.pwms.append(PWM(Pin(pin2)))
        for pwm in self.pwms:
            # Lower frequencies sound clearer, but can have a bit of a high pitched buzzing sometimes
            pwm.freq(160_000)
            pwm.duty_u16(0)

        # Initialize timer 1 (arbitrary choice) to sample rate
        mem32[_DMA_MEM_TIM0] = timer_fraction_for_rate(rate)

        # Find PWM slice our pin is in
        pwm_slice = pin_2_pwm_slice(pin)
        # Read the top (wrap around) value for our PWM slice
        self.pwm_top = mem32[mem_addr_top_for_pwm_slice(pwm_slice)]
        print(f"{self.pwm_top=}")
        # Store the address for our PWM slice's compare value
        self.pwm_compare_addr = mem_addr_compare_for_pwm_slice(pwm_slice)

        self.dma = DMA()
        self.dma_ctrl = self.dma.pack_ctrl(
            size=2,                   # 32bit word
            inc_read=True,            # increment read addr
            inc_write=False,          # dont increment write addr
            treq_sel=_DMA_FLAG_TIM0,  # use dma pacing timer 1 (arbitrarily)
            bswap=False,               # swap the bytes when writing
            irq_quiet=False,          # dont quiet the irq
        )
        self.dma.irq(self._handle_write)

        super().__init__(channels=channels, rate=rate)
        self._handle_write(None)


    @staticmethod
    @micropython.viper
    def erase_buffer(buf):
        """Reset the given buffer to a neutral signal."""
        _NEUTRAL = const((32767 << 16) | 32767)
        buf_len = int(len(buf)) // 4
        buf_ptr = ptr32(buf)
        i = 0
        while i < buf_len:
            buf_ptr[i] = int(_NEUTRAL)
            i += 1


    @staticmethod
    @micropython.viper
    def scale_samples(buf, top: int):
        """Scale samples into range of 0-pwm_top."""
        buf_len = int(len(buf)) // 2
        buf_ptr = ptr16(buf)
        i = 0
        while i < buf_len:
            buf_ptr[i] = buf_ptr[i] * top // 65535
            i += 1


    def _handle_write(self, _):
        """IRQ for DMA; write data with dma and ready the next data to write."""
        self.dma.config(
            read=self.mvs[0],
            write=self.pwm_compare_addr,
            count=self.buf_size // 4,
            ctrl=self.dma_ctrl,
            trigger=True,
        )
        self.mvs.reverse()

        mv = self.mvs[0]
        self.erase_buffer(mv)
        self.fill_buffer(mv)
        self.scale_samples(mv, self.pwm_top)


    def deinit(self):
        """De-initialize the audio output."""
        self.dma.irq(None)
        for pwm in self.pwms:
            pwm.duty_u16(0)
        super().deinit()
