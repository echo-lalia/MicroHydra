"""Audio sources for audio module.

The `Source` class is intended to provide some common functionality,
but should be subclassed to supply an `add_to_buffer` method for a specific source type.
The `add_to_buffer` method uses `mh_if` statements to conditionally convert audio from the source format,
into the format required by the Output module.

The `get_source` function can be used to dynamically import and return the Source class
required to decode a source data type (if it exists).


The funcion of this module (especially the use of pre-calculated `PERIODS` for changing the pitch of source samples)
heavily pulls from the `m5sound` module written/contributed by Mavica:

#/*
# * ----------------------------------------------------------------------------
# * "THE BEER-WARE LICENSE" (Revision 42 modified):
# * <maple@maple.pet> wrote this file.  As long as you retain this notice and
# * my credit somewhere you can do whatever you want with this stuff.  If we
# * meet some day, and you think this stuff is worth it, you can buy me a beer
# * in return.
# * ----------------------------------------------------------------------------
# */

"""
# ruff: noqa: PLC0415

from .source import Source


# Maintain a dictionary to cache imported audio source classes (faster than re-importing each time)
_sources = {}


def get_source(*, channels: int = 1, signed: bool = True, sample_bits: int = 16) -> type[Source]:
	"""Return the audio Source subclass that handles the defined input data."""
	src_def = (channels, signed, sample_bits)
	if src_def in _sources:
		return _sources[src_def]

	if src_def == (1, True, 16):
		from .monoint16 import MonoInt16Source as SrcCls

	else:
		raise NotImplementedError(f"Audio Source ({channels=}, {signed=}, {sample_bits=}) has no implementation.")

	_sources[src_def] = SrcCls
	return SrcCls
