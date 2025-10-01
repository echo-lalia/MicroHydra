"""This module wraps lib/audio with a simple API for making square wave beeps.

Known issue:
  The audio produced in this version of beeper.py is much higher quality than
  it was in previous versions (thanks to the precision of mavica's I2SSound module),
  but there is a noticeable delay due to the somewhat infrequent updating of the I2S IRQ.
  At the time of writing I am not sure how I might fix that.

  I have already tried:
  - Instantly calling the IRQ handler function after playing a sound. This does make the
    sound happen faster, but also makes the timing very inconsistent and strange sounding.
  - Calling the IRQ handler AND setting a timer to stop the audio, but this sounds horrible
    when multiple sounds happen rapidly.
  - Unregistering/reregistering the IRQ function with I2S. This seems to cause a silent
    crash of MicroPython for some reason.
"""

from machine import Timer

from lib.audio import Audio
from .config import Config
from .utils import get_instance


_SQUARE = const(\
    b'\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80'
    b'\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80'
    b'\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80'
    b'\x00\x80\x00\x80\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F'
    b'\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F'
    b'\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F'
    b'\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\x00\x80'
)
SQUARE = memoryview(_SQUARE)



def note_to_int(note:str) -> int:
    """Convert a note string into an integer for I2SSound.

    Note should be a string containing:
    - A letter from A-G,
    - Optionally, a 'S' or '#' selecting a 'sharp' note,
    - An octave (as an integer).

    Examples: 'C4', 'CS5', 'G3'
    """
    note = note.upper()

    # Extract the pitch and the octave from the note string
    pitch = note[0]
    octave = int(note[-1])

    # Define the base values for each pitch
    base_values = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

    # Calculate the base value for the note
    value = base_values[pitch]

    # Adjust for sharps
    if 'S' in note \
    or '#' in note:
        value += 1

    # Calculate the final integer value
    # C4 is the reference point with a value of 0
    return value + (octave - 4) * 12




class Beeper:
    """A class for playing simple UI beeps."""

    def __init__(self):
        """Initialize the Beeper (and I2SSound)."""
        self.audio = get_instance(Audio)
        self.config = get_instance(Config)
        self.note_buf = []
        self.timer = Timer(3)


    def stop(self):
        """Stop all channels."""
        for i in range(self.audio.channels):
            self.audio.stop(channel=i)


    def play_next(self, tim=None):  # noqa: ARG002
        """Play the next note (on callback)."""
        self.stop()

        if not self.note_buf:
            self.timer.deinit()
            return

        notes, volume, time_ms = self.note_buf.pop(0)

        for idx, note in enumerate(notes):
            self.audio.play(
                sample=SQUARE,
                note=note_to_int(note),
                volume=volume,
                channel=idx,
                loop=True,
                )

        self.timer.init(mode=Timer.ONE_SHOT, period=time_ms, callback=self.play_next)


    def play(self, notes, time_ms=100, volume=None):
        """Play the given note.

        This is the main outward-facing method of Beeper.
        Use this to play a simple square wave over the I2C speaker.

        "notes" should be:
        - a string containing a note's name
            notes="C4"
        - an iterable containing a sequence of notes to play
            notes=("C4", "C5")
        - an iterable containing iterables, each with notes that are playes together.
            notes=(("C4", "C5"), ("C6", "C7"))

        "time_ms" is the time in milliseconds to play each note for.

        "volume" is an integer between 0 and 10 (inclusive).
        """
        if not self.config['ui_sound']:
            return
        if volume is None:
            volume = self.config['volume'] + 5

        if isinstance(notes, str):
            notes = [notes]

        for note in notes:
            if isinstance(note, str):
                note = (note,)
            self.note_buf.append((note, volume, time_ms))

        self.play_next()
