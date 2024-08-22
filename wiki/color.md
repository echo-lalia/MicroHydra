## hydra.color

This module contains some color logic used by MicroHydra.  
Previously these functions lived in `lib.microhydra` (or in `lib.st7789py`).



## Color mixing functions:

`mix_color565(color1, color2, mix_factor=0.5, hue_mix_fac=None, sat_mix_fac=None)`
> High quality mixing of two rgb565 colors, by converting through HSV color space.
> <br />
<br />

`darker_color565(color, mix_factor=0.5)`
> Get a darker version of a 565 color.
> <br />
<br />

`lighter_color565(color, mix_factor=0.5)`
> Get a lighter version of a 565 color.
> <br />
<br />

`color565_shiftred(color, mix_factor=0.4, hue_mix_fac=0.8, sat_mix_fac=0.8)`
> Simple convenience function which shifts a color toward red.
> This was made for displaying 'negative' ui elements, while sticking to the central color theme.
> <br />
<br />

`color565_shiftgreen(color, mix_factor=0.1, hue_mix_fac=0.4, sat_mix_fac=0.1)`
> Simple convenience function which shifts a color toward green.
> This was made for displaying 'positive' ui elements, while sticking to the central color theme.
> <br />
<br />

`color565_shiftblue(color, mix_factor=0.1, hue_mix_fac=0.4, sat_mix_fac=0.2)`
> Simple convenience function which shifts a color toward blue.
> <br />
<br />

`compliment_color565(color)`
> Generate a complimentary color from given RGB565 color.
> <br />
<br />


## Conversion functions:

`color565(r:int, g:int, b:int) -> int`  
> Convert 24bit (0-255) RGB values into 16bit 565 format.  
> Returns a single 565-encoded integer.  
> <br />
<br />

`separate_color565(color)`
> Separate a 16-bit 565 encoding into red, green, and blue components.
> <br />
<br />

`combine_color565(red, green, blue)`
> Combine red, green, and blue components into a 16-bit 565 encoding.
> <br />
<br />

`rgb_to_hsv(r, g, b)`
> Convert an RGB float to an HSV float.
> <br />
<br />

`hsv_to_rgb(h, s, v)`
> Convert an HSV float to an RGB float.
> <br />
<br />


## Misc functions:

`swap_bytes(color:int) -> int`
> Swap the left and right bytes in a 16 bit color.  
> This is mainly used internally to unswap colors that would be swapped when writing to the display.  
> <br />
<br />

`mix(val2, val1, fac=0.5)`
> Mix two values to the weight of `fac` 
> <br />
<br />

`mix_angle_float(angle1, angle2, factor=0.5)`
> Take two angles as floats (range 0.0 to 1.0) and average them to the weight of `factor`.
> Mainly for blending hue angles.
> <br />
<br />

