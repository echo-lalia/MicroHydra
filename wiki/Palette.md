## lib.display.Palette

This Palette class is designed to be used for storing a list of RGB565 colors,
and for returning the apropriate colors by index to be used with MicroHydra's display module.

When `Config` from `lib.hydra.config` is initialized, it reads the user set color data from `config.json` and creates a 16-color palette from it.

<br />

Key notes on Palette:
  - Has a static length of 16 colors

  - Is used by both `lib.hydra.config.Config` and `lib.display.Display` (it is the same Palette in both)
  
  - uses a bytearray to store color information,
    this is intended for fast/easy use with Viper's ptr16.

  - Returns an RGB565 color when using normal framebuffer, or an index when Display is initialized with `use_tiny_buf`.
    (This makes it so that you can pass a `Palette[i]` to the Display class in either mode.)
    
  - Palette is a singleton, which is important so that different MH classes can modify and share it's data
    (without initializing the Display).


Retrieving a color from the Palette is fairly fast, but if you want to maximize your speed, it's probably smart to read and store the colors you need as local variables (after initializing the `Display` and `Config`).

<br />

For your reference, here is a complete list of the colors, by index, contained in the palette:
<ol start="0">
  <li>Black</li>
  <li>Darker bg_color</li>
  <li>bg_color</li>
</ol>

<ol start="3">
  <li>84% bg_color 16% ui_color</li>
  <li>67% bg_color 33% ui_color</li>
  <li>50% bg_color 50% ui_color (mid_color)</li>
  <li>33% bg_color 67% ui_color</li>
  <li>16% bg_color 84% ui_color</li>
</ol>

<ol start="8">
  <li>ui_color</li>
  <li>Lighter ui_color</li>
  <li>white</li>
</ol>

<ol start="11">
  <li>reddish bg_color</li>
  <li>greenish mid_color</li>
  <li>bluish ui_color</li>
</ol>

<ol start="14">
  <li>compliment bg_color (opposite hue)</li>
  <li>compliment ui_color</li>
</ol>

<br /><br />
