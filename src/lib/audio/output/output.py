"""Base audio output class."""
from lib.audio.source.source import Source



class Output:
    """The base audio output class.

    This class is not intended to be used directly.
    It must be subclassed to add support for specific audio output devices.
    """

    def __init__(
            self,
            channels: int = 4,
            rate: int = 11025,
            ):
        """Initialize the Output device.

        channels:
            the number of concurrent audio channels to allow.
        rate:
            The sample rate to use for output (should usually match the sample rate of the source).
        """
        self.rate = rate
        self.num_channels = channels
        self.channels = [None] * channels


    @micropython.viper
    def prune_buffers(self):
        """Remove any finished sources from our channels."""
        channels = self.channels
        num_channels = int(self.num_channels)
        i = 0
        while i < num_channels:
            chan = channels[i]
            if chan and chan.finished:
                chan.stop()
                channels[i] = None
            i += 1


    def deinit(self):
        """De-initialize the audio output."""
        for channel in self.channels:
            if channel is not None:
                channel.stop()


    @micropython.viper
    def fill_buffer(self, buf) -> bool:
        """Fill buffer using each held sample.

        Returns True if any sources wrote to the buffer.
        """
        num_channels = int(self.num_channels)
        wrote_any = False
        i = 0
        while i < num_channels:
            chan = self.channels[i]
            if chan:
                chan.add_to_buffer(buf)
                wrote_any = True
            i += 1
        return wrote_any


    def _auto_select_channel(self) -> int:
        """Select the next free channel, or channel 0."""
        for idx, chan in enumerate(self.channels):
            if chan is None:
                return idx
        return 0


    def play(
            self,
            source: Source,
            channel: int|None = None,
        ):
        """Insert the given audio source into a channel, playing it immediately.

        - source:
            The audio source to play.
            Expected to be of type lib.audio.source.Source
        - channel:
            Channel the sample should play on,
            by default, it will use the first free channel, or override channel 0.
        """
        if channel is None:
            channel = self._auto_select_channel()

        if self.channels[channel] is not None:
            self.channels[channel].stop()

        self.channels[channel] = source


    def stop(
            self,
            channel: int|None = None,
        ):
        """Stop playing audio.

        If a channel is given, stops that channel. Otherwise, stops all channels.
        """
        if channel is None:
            for i in range(self.num_channels):
                self.stop(i)
            return
        self.channels[channel].stop()
        self.channels[channel] = None

