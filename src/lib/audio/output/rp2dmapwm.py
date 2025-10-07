# mh_include_if rp2 and pwm_speaker:
"""Play PWM audio by using DMA to write samples to the RP2040's PWM register.

This module was written for the PicoCalc, with a Raspberry Pi Pico.
However, I would like to add support the Pico2 / RP2350 as well.
(and I hope it can work with devices other than the PicoCalc, too)

The RP2040 has 8 PWM slices, each with 2 channels (each slice has 2 separate 16bit counter and compare values).
For speed and simplicity (and possibly necessity) this module writes to *both* channels using a single 32-bit word.
This simplifies stereo playback, but it's also important because the DMA peripheral seems to
always write a 32-bit word (duplicating 8 or 16bit words to fit the space).


"""



