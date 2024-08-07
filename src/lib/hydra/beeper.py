from lib.audio import Audio
from lib.hydra.config import Config
from machine import Timer



_SQUARE = const(\
    b'\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80'\
    b'\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80'\
    b'\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80\x00\x80'\
    b'\x00\x80\x00\x80\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F'\
    b'\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F'\
    b'\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F'\
    b'\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\xFF\x7F\x00\x80'
)
SQUARE = memoryview(_SQUARE)



def note_to_int(note:str) -> int:
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
    final_value = value + (octave - 4) * 12
    
    return final_value

    


class Beeper:
    
    def __init__(self):
        self.audio = Audio.instance if hasattr(Audio, 'instance') else Audio()
        self.config = Config.instance if hasattr(Config, 'instance') else Config()
        self.note_buf = []
        self.timer = Timer(-1)
    
    
    def stop(self):
        for i in range(self.audio.channels):
            self.audio.stop(channel=i)
    

    def play_next(self, tim=None):
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
        """
        This is the main outward-facing method of Beeper.
        Use this to play a simple square wave over the SPI speaker.
        
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


if __name__ == "__main__":
    import time
    from lib import userinput
    
    user_input = userinput.UserInput()
    beep = Beeper()
    
    
#     beep.play(
#         (
#             ("G3"),
#             ("G3", "C4"),
#             ("G3", "C4", "E4"),
#             ("G3", "C4", "E4", "A4"),
#             ("C4", "E4", "A4"),
#             ("E4", "A4"),
#             ("A4"),
#         ),
#         time_ms=400,
#         volume=10,
#         )

    beep.play(
        (
            ("C3"),
            ("C3", "C#3"),
            ("c3", "cs3"),
            "C4",
        ),
        time_ms=400,
        )
    
#     correct = 0
#     incorrect = 0
#     for key, val in tone_map.items():
#         if val != note_to_int(key):
#             print("tone map: ", key, val)
#             print("note_to_int: ", note_to_int(key))
#             incorrect += 1
#         else:
#             correct += 1
    
#     print(f"\nCorrect notes: {correct}")
#     print(f"Incorrect notes: {incorrect}")
    
    time.sleep(1)
    
