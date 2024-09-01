Currently, MicroHydra supports 2 devices (the Cardputer and the TDeck), with the intention to add more in the future.  

<br/>



# Cardputer
The M5Stack Cardputer is the device MicroHydra was [first designed](https://github.com/echo-lalia/MicroHydra/wiki/MH-Origins) for.  

### Pros:
* Because it was the first device supported by MicroHydra, most of the features are heavily geared towards this form-factor,
  and feel very comfortable on the Cardputer, specifically.

### Cons:
* The 512kb of RAM on the Cardputer can sometimes feel very limiting in MicroHydra. 

<br/>



# TDeck
> ***Important note:** The keyboard that comes with the TDeck has a separate ESP32-C3 which communicates with the main ESP32-S3 through I²C.*
> *The firmware that comes on the keyboard does not allow many features MicroHydra requires,  
> (Keys can't be held, modifier keys do nothing, not many symbols can be typed etc).  
> *I have made an [updated firmware](https://github.com/echo-lalia/t-deck-keyboard-hydra), which adds several key features,
> including the ability to enable a 'raw' output to the main MCU, while maintaining backwards-compatibility with the old firmware.*
> *In order to flash this firmware, you must solder pins, and connect a **USB to TTL converter** onto the TDeck, which I found very annoying to do.*
>
> *The `_keys` module for the TDeck does also have a backwards-compatibility mode for when it doesn't detect the new firmware. However, the experience is sub-par.*

The Lilygo T-Deck was chosen as the second device to support because it had the same ESP32-S3 MCU, and ST7789 display as the Cardputer.  
*(Also, I just thought it looked neat.)*

### Pros:
* The 8MB of octal SPI-RAM means you practically never have to worry about memory usage in TDeck apps.
* Touch support for the built-in apps was added for the T-Deck, and works fairly well.

### Cons:
* The trackball on the T-Deck is not very accurate, and is slightly hard to control on some menus.
* The default keyboard firmware is bad, and must be updated to get all the features. This involves soldering and using a USB to TTL adapter.
* The keyboard has fewer keys than the Cardputer, and the legend on the keyboard varies randomly between units,
  so you need to memorize certain key-combos to get full use out of it.

