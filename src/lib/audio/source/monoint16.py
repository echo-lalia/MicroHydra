"""Sources for reading single channel 16bit samples."""
from .source import Source, PERIODS


_INT_MINVAL = const(-32768)
_INT_MAXVAL = const(32767)

_INT_MINVAL_TARGET = const(0)
_INT_MAXVAL_TARGET = const(65535)



class MonoInt16Source(Source):
    """Source for reading from a memoryview with a single channel of signed 16bit samples."""

    # mh_if stereo_uint16_audio:
    @micropython.viper
    def add_to_buffer(self, buffer) -> int:
        """Convert source data, add that data to the given buffer, and return bytes written.
        
        Converts mono signed 16bit data to stereo unsigned 16bit data.
        """
        if bool(self.finished):
            return 0
        # period is a bytes object containing information about how many source frames to advance per output frame, for our given note.
        period_ptr = ptr8(PERIODS[self.note])
        period_len = int(len(PERIODS[self.note]))
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

        target_buf_ptr = ptr32(buffer)
        target_buf_len = int(len(buffer)) // 4
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
            if source_frame >= 32768:
                source_frame -= 65536
            source_frame += 32768


            # Extract left/right channels from target, and add our source sample to each (l/r might actually be mislabelled here, but it doesn't matter)
            target_frame_l = target_buf_ptr[target_frame_idx] >> 16
            target_frame_r = target_buf_ptr[target_frame_idx] & 0b1111_1111_1111_1111
            target_frame_l += source_frame
            target_frame_r += source_frame
            # Enforce maximum value on both channels
            if target_frame_l > _INT_MAXVAL_TARGET:
                target_frame_l = _INT_MAXVAL_TARGET
            if target_frame_r > _INT_MAXVAL_TARGET:
                target_frame_r = _INT_MAXVAL_TARGET

            # Recombine l/r channels and set them in the target buffer
            target_buf_ptr[target_frame_idx] = int((target_frame_l << 16) | target_frame_r)


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
                            return target_frame_idx * 4
                        source_buf_end = int(self.mv_end) // 2
                    # If not in file mode, we either loop, or end the playback at the end of the buffer.
                    elif not loop:
                        self.finished = True
                        return target_frame_idx * 4
                    source_frame_idx = 0

                i += 1


            target_frame_idx += 1
        
        # Wrote a bunch of target frames
        self.period_idx = period_idx
        self.frame_idx = source_frame_idx

        return target_frame_idx * 4

    # mh_end_if
    
