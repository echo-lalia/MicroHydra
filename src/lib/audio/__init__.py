"""MicroHydra audio module.

This module provides a simple API for accessing audio features in MicroHydra.
"""
from .source import Source, get_source

# i2s constants
_MH_I2S_SCK = const(7)
_MH_I2S_WS = const(5)
_MH_I2S_SD = const(6)
# pwm constants
_MH_PWM_OUT = const(26)
_MH_PWM_OUT_2 = const(27)

# mh_if i2s_speaker:
# from .output.i2s import I2SOutput as Output

# mh_else_if pwm_speaker and rp2:
from .output.rp2dmapwm import Rp2DmaPwmOutput as Output

# mh_end_if





class Audio:
    """Utility for playing sound using a hardware-specific output module."""

    def __new__(cls, **_kwargs):  # noqa: D102
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance


    def __init__(self, buf_size=1024, rate=11025, channels=4):
        """Create the Audio object.

        Args: (Passed to driver module)
            buf_size: The buffer size to use
            rate: The sample rate for the audio
            channels: The number of simultaneous audio channels
        """
        # mh_if i2s_speaker:
        # self.out = Output(
        #     sck=_MH_I2S_SCK,
        #     ws=_MH_I2S_WS,
        #     sd=_MH_I2S_SD,
        #     channels=channels,
        #     rate=rate,
        #     buf_size=buf_size,
        # )

        # mh_else_if pwm_speaker:
        self.out = Output(
            pin=_MH_PWM_OUT,
            pin2=_MH_PWM_OUT_2,
            channels=channels,
            rate=rate,
            buf_size=buf_size,
        )

        # mh_end_if

        # Allow calling the `stop` method from Output object directly on the Audio object.
        self.stop = self.out.stop


    @staticmethod
    def make_source(
        source: memoryview|str,
        *,
        source_channels: int = 1,
        source_signed: bool = True,
        source_bits: int = 16,
        volume: int = 10,
        note: int = 0,
        octave: int = 4,
        loop: bool = False,
        buf_size: int = 512,
        ) -> Source:
        """Return a Source object for the provided sample.

        source:
            The audio source to read data from. Expected to be a memoryview, file path, or file object.
            It will be wrapped by a `Source` object whos type will be chosen by the provided `source_...` options.
        source_channels:
            The number of channels represented by the source data. (1 for mono, 2 for stereo) (default: 1)
        source_signed:
            Whether or not the source represents signed data (rather than unsigned data) (default: True)
        source_bits:
            The bit-width of the audio samples contained in `source` (default: 16)
        volume:
            The volume of the sample, from 0-10 (inclusive), where 0 is silent, and 10 is full volume (default: 10)
        note:
            The note to play (controls the pitch of the audio). 0 corrisponds to an unaltered sample.
            `note` is usally in the range 0-12 (exclusive) which maps to notes C to B.
            Values outside that range are also valid, and will affect the octave. (default: 0)
        octave:
            The octave for the sample to play (controls the pitch of the audio).
            Default is 4, which (if `note` is also 0) corrisponds to an unaltered sample.
        loop:
            Whether the sample should loop (or just play once) (default: False)
        buf_size:
            The size (in bytes) of the buffer to use for loading samples from a file (default: 512)
        """
        return get_source(
            channels=source_channels,
            signed=source_signed,
            sample_bits=source_bits,
        )(
            source,
            note=note,
            octave=octave,
            loop=loop,
            volume=volume,
            buf_size=buf_size,
        )


    def play(
            self,
            source: Source|memoryview|str,
            channel: int|None = None,
            **kwargs,
        ):
        """Play audio from the given source.

        source:
            The audio source to read data from. Expected to be a Source, memoryview, file path, or file object.
            If this isnt a `Source`, it will be wrapped by a `Source` object,
            whos type will be chosen by the provided `source_...` kwargs.
        channel:
            The output channel to play the sample on.
            Should be within the range specified by `channels` when constructing the `Audio` object.
            Defaults to `None`, which selects the next free audio channel, or 0 if all are used.
        **kwargs:
            Optional keyword arguments to pass to the `get_source` method (if `source` isn't already a `Source`).
            (see `Audio.make_source` for possible options).
        """
        if not isinstance(source, Source):
            source = self.make_source(source, **kwargs)
        self.out.play(source, channel=channel)
