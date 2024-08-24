There are two main modules built-in to MicroHydra currently, which can be used for playing sound on the Cardputer. 


<br />

### lib.audio.Audio
MicroHydra's [audio](https://github.com/echo-lalia/Cardputer-MicroHydra/tree/main/src/lib/audio) module subclasses the apropriate audio module for the current device (Currently this is only `i2ssound`, but may be expanded in the future), and initializes it with the apropriate values for the device.

Note:  
> *`i2ssound` was previously named `M5Sound`, and was contributed by [Lana-chan](https://github.com/echo-lalia/Cardputer-MicroHydra/commits?author=Lana-chan), for playing high-quality sound on the Cardputer.  
> It has been renamed for consistency with MicroHydras other modules.*

It can play samples stored in a variable, or read large samples from storage using little memory.  
It also can change the pitch of those samples, and even play several at the same time, overlapping.

<br />

*basic usage example (ALSO provided by Lana-chan):*


``` Python
import time
from lib.audio import Audio

audio = Audio()

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
    audio.play(SQUARE, note, 0, 14, 0, True)
    for i in range(13,1,-1): # fade out volume
        audio.setvolume(i)
        time.sleep(0.05)
    audio.stop(0)
```

Samples can also be loaded from a 'raw' file on the flash or SDCard. 

``` Python
i2ssound.Sample(source, buffer_size=1024)
"""Initialize a sample for playback

- source: If string, filename. Otherwise, use MemoryView.
- buffer_size: If loading from filename, the size to buffer in RAM.
"""
```

-----

<br /><br /><br />

### beeper
[beeper.py](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/main/src/lib/hydra/beeper.py) is a module for playing simple UI beeps.

This module is very imperfect. It is somewhat limited in its use, however, it *is* simple to use.  
> In previous versions, this module used its own, blocking, implementation for sending audio to the speaker. However, the current version is just a wrapper for the `Audio` class above. The audio is now much higher quality and more consistent, however there is a noticable delay in it. I would like to fix this in the future, but I'm not sure how to do that. 



To use it: 

``` Python
from lib.hydra import beeper
```   

``` Python
#init the beeper!
beep = beeper.Beeper()

beep.play(
    # a tuple of strings containing notes to play. a nested tuple can be used to play multiple notes together.
    notes=('C4',('D4','D4')),
    # how long to play each note
    time_ms=120,
    # an integer from 0-10 representing the volume of the playback. Default is 2, 0 is almost inaudible, 10 is loud.
    volume=10,
) 
```

<br /><br /><br />

