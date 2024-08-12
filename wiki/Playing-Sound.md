There are two main modules built-in to MicroHydra currently, which can be used for playing sound on the Cardputer. 


<br />

### M5Sound.py
[M5Sound](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/main/MicroHydra/lib/M5Sound.py) is a module contributed by [Lana-chan](https://github.com/echo-lalia/Cardputer-MicroHydra/commits?author=Lana-chan) for playing high-quality sound on the Cardputer.

It can play samples stored in a variable, or read large samples from storage using little memory.   
It also can change the pitch of those samples, and even play several at the same time, overlapping. Unlike the beeper module, this one is non-blocking (your code can continue to execute while sound is playing).

<br />

*basic usage example (ALSO provided by Lana-chan):*


``` Python
import time
from lib import M5Sound

sound = M5Sound.M5Sound()

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

for note in range(24,60): # note values, C-3 to B-5
    sound.play(SQUARE, note, 0, 14, 0, True)
    for i in range(13,1,-1): # fade out volume
        sound.setvolume(i)
        time.sleep(0.05)
    sound.stop(0)
```

Samples can also be loaded from a 'raw' file on the flash or SDCard. 

``` Python
M5Sound.Sample(source, buffer_size=1024)
"""Initialize a sample for playback

- source: If string, filename. Otherwise, use MemoryView.
- buffer_size: If loading from filename, the size to buffer in RAM.
"""
```

-----

<br /><br /><br />

### beeper
[beeper.py](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/main/MicroHydra/lib/beeper.py) is a module for playing simple UI beeps.

This module is very imperfect. It is somewhat limited in its use, and it uses more memory than what is probably needed. However, it *is* simple to use, and it thankfully does work decent for short UI tones.



To use it: 

``` Python
from lib import beeper
```   

``` Python
#init the beeper!
beep = beeper.Beeper()

beep.play(
    notes=('C4',('D4','D4')), # a tuple of strings containing notes to play. a nested tuple can be used to play multiple notes together.
    time_ms=120, # how long to play each note
    volume=4) # an integer from 0-10 representing the volume of the playback. Default is 2, 0 is almost inaudible, 10 is loud.
```

<br /><br /><br />

