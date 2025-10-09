"""Sources for reading single channel 16bit samples."""
from .source import Source, PERIODS


_INT16_MINVAL = const(-32768)
_INT16_MAXVAL = const(32767)

_UINT16_MAXVAL = const(65535)

_BYTES_PER_SOURCE_FRAME = const(2)

# mh_if stereo_uint16_audio:
_BYTES_PER_TARGET_FRAME = const(4)
# mh_else:
# _BYTES_PER_TARGET_FRAME = const(2)
# mh_end_if


class MonoInt16Source(Source):
    """Source for reading from a memoryview with a single channel of signed 16bit samples."""

    @micropython.viper
    def add_to_buffer(self, buffer) -> int:
        """Convert source data, add that data to the given buffer, and return bytes written.

        Converts mono signed 16bit data to stereo unsigned 16bit data.
        """
        if bool(self.finished):
            return 0
        # period tells us how many source frames to advance per output frame, for our given note.
        period_ptr = ptr8(self.period)
        period_len = int(len(self.period))
        period_idx = int(self.period_idx)
        period_repeat = int(self.period_repeat)

        # Our source data buffer, and our current position in that source buffer.
        source_buf_ptr = ptr16(self.mv)
        source_buf_len = int(len(self.mv)) // 2
        source_buf_end = int(self.mv_end) // 2
        source_frame_idx = int(self.frame_idx)

        file_mode = bool(self.file_mode)
        loop = bool(self.loop)
        vol_shift = int(self.vol_2_shift(self.volume))

        # mh_if stereo_uint16_audio:
        target_buf_ptr = ptr32(buffer)
        target_buf_len = int(len(buffer)) // _BYTES_PER_TARGET_FRAME

        # mh_else_if mono_int16_audio:
        # target_buf_ptr = ptr16(buffer)
        # target_buf_len = int(len(buffer)) // _BYTES_PER_TARGET_FRAME

        # mh_else:
        # raise NotImplementedError("Audio output for this source/output format hasn't been implemented yet.")
        # mh_end_if


        target_frame_idx = 0

        # Loop over target buffer
        while target_frame_idx < target_buf_len:

            # Ensure we have data to work with
            if source_frame_idx >= source_buf_end:
                self.load_from_file()
                if bool(self.finished):
                    return target_frame_idx * 4
                source_buf_end = int(self.mv_end) // 2

            # Get our source audio frame
            source_frame = source_buf_ptr[source_frame_idx]
            # Source value is signed but incorrectly interpreted as an unsigned int.
            # If value is higher than the signed integer limit, it's meant to be negative.
            if source_frame > _INT16_MAXVAL:
                source_frame -= 65536


            # Apply the volume
            source_frame >>= vol_shift


            # mh_if stereo_uint16_audio:
            # Convert mono signed 16bit audio into stereo unsigned 16bit audio.
            # Extract left/right channels from target (l/r might actually be mislabelled here)
            target_frame_l = (target_buf_ptr[target_frame_idx] >> 16) & 0xffff
            target_frame_r = (target_buf_ptr[target_frame_idx] & 0xffff)
            # source_frame is signed; adding will either decrease or increase frame value
            target_frame_l += source_frame
            target_frame_r += source_frame

            # Enforce maximum value on both channels
            if target_frame_l < 0:
                target_frame_l = 0
            elif target_frame_l > _UINT16_MAXVAL:
                target_frame_l = _UINT16_MAXVAL
            if target_frame_r < 0:
                target_frame_r = 0
            elif target_frame_r > _UINT16_MAXVAL:
                target_frame_r = _UINT16_MAXVAL


            # Recombine l/r channels and set them in the target buffer
            target_buf_ptr[target_frame_idx] = int(int(target_frame_l << 16) | target_frame_r)

            # mh_else_if mono_int16_audio:
            # # clamp and write signed int16 audio to buffer
            # target_frame = target_buf_ptr[target_frame_idx]
            # target_frame += source_frame
            # if target_frame < _INT16_MINVAL:
            #     target_frame = _INT16_MINVAL
            # elif target_frame > _INT16_MAXVAL:
            #     target_frame = _INT16_MAXVAL
            # target_buf_ptr[target_frame_idx] = target_frame & 0xffff

            # mh_end_if


            # Advance the source frame as defined by our pre-generated period, to achieve a target pitch
            i = 0  # iterate over period_repeat
            while i < period_repeat:
                source_frame_idx += period_ptr[period_idx]
                period_idx += 1
                if period_idx >= period_len:
                    period_idx = 0

                # What happens when we reach the end of the source buffer?
                if source_frame_idx >= source_buf_len:
                    # In file mode, `self.finished` is controlled by `self.load_from_file()`.
                    if file_mode:
                        self.load_from_file()
                        if bool(self.finished):
                            return target_frame_idx * _BYTES_PER_TARGET_FRAME
                        source_buf_end = int(self.mv_end) // 2
                    # If not in file mode, we either loop, or end the playback at the end of the buffer.
                    elif not loop:
                        self.stop()
                        return target_frame_idx * _BYTES_PER_TARGET_FRAME
                    source_frame_idx = 0

                i += 1


            target_frame_idx += 1

        # Wrote a bunch of target frames
        self.period_idx = period_idx
        self.frame_idx = source_frame_idx

        return target_frame_idx * _BYTES_PER_TARGET_FRAME
