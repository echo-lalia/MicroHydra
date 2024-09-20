"""MicroHydra audio module.

This module provides a simple API for accessing audio features in MicroHydra.
"""

from .i2ssound import I2SSound


_MH_I2S_SCK = const(7)
_MH_I2S_WS = const(5)
_MH_I2S_SD = const(6)



class Audio(I2SSound):
    """General wrapper for specific sound module."""

    def __new__(cls, **kwargs):  # noqa: ARG003, D102
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, buf_size=2048, rate=11025, channels=4):
        """Create the Audio object.

        Args: (Passed to driver module)
            buf_size: The buffer size to use
            rate: The sample rate for the audio
            channels: The number of simultaneous audio channels
        """
        super().__init__(
            buf_size=buf_size,
            rate=rate,
            channels=channels,
            sck=_MH_I2S_SCK,
            ws=_MH_I2S_WS,
            sd=_MH_I2S_SD,
            )
