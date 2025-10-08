

class Output:
    def __init__(
            self,
            channels: int = 4,
            rate: int = 11025,
            ):
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
