
### lib.userinput.UserInput

[userinput](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/wikiimprovements/src/lib/userinput/userinput.py) provides a all of a devices physical inputs in one place.

At its core, the module is based on the device-specific `_keys` module, which provides logic for reading the keypresses and converting them into readable strings. The `UserInput` class subclasses the `_keys.Keys` class, and inherits those device-specific features.  
`UserInput` can also provide other kinds of input, such as providing touch data from a device with a touchscreen. These extra features, of course, are based on the specific device being used.

The `UserInput` class also handles key-repeating behaviour, and locking modifier keys. 

> *This module was previously the `lib.smartkeyboard` module. It has been renamed and expanded for MicroHydra 2.x to support different devices and input methods.*


<br/><br/>

# UserInput:

## Constructor:

`userinput.UserInput(hold_ms=600, repeat_ms=80, use_sys_commands=True, allow_locking_keys=False, **kwargs)`  
> Creat the object for accessing user inputs.
> 
> Args:
> * `hold_ms`:  
>   The amount of time, in milliseconds, a key must be held before it starts to repeat.
>   
> * `repeat_ms`:  
>   While a key is being held and repeating, how long between repetitions.
>
> * `use_sys_commands`:  
>   Whether or not to enable keyboard shortcuts for built-in system commands
>
> * `allow_locking_keys`:  
>   Whether or not to allow modifier keys to 'lock' (stay activated when tapped). This draws an overlay on the screen using the display module.
>   
> * `**kwargs`:  
>   Any other keyword args given are passed along to the `_keys.Keys` class, allowing for device-specific options to be used.
> <br />

<br />

## Read keys:

`UserInput.get_pressed_keys()`  
> Return a list of strings, representing the names of keys that are currently being pressed.
> <br />
<br />

`UserInput.get_new_keys()`  
> Return a list of strings, representing the names of keys that are newly pressed (are now pressed but were not pressed last time we checked).
> 
> This method also runs additional logic based on the settings provided in the constructor:  
> - key repeating logic:  
>   Keys will return when they are new, *and* periodically after they have been held down for the time specified by `UserInput.hold_ms`
> 
> - locking keys logic:  
>   When `allow_locking_keys` is `True`, if a modifier key is pressed without pressing another key, that key will be 'locked', and held until it is pressed again.  
>   This also draws an overlay (displaying the locked keys) to the screen using a callback every time `Display.show()` is called.
> 
> <br />
<br />

`UserInput.get_mod_keys()`  
> Return a list of modifier keys that are being held, including keys that are locked if `allow_locking_keys` is `True`.
> <br />
<br />

<br /><br />


## Read touch:
*These methods only exist when the device has a touchscreen*

`UserInput.get_current_points()`  
> Return the current touch data in the form of a list of `TouchPoints`  
> Touchpoints are `namedtuple`s with the following format:  
> `namedtuple("TouchPoint", ["id", "x", "y", "size"])`
> <br />
<br />

`UserInput.get_touch_events()`  
> Similar to `get_new_keys`, this method does some pre-processing on touch data to make it easier to parse.
> 
> Touch events are only returned once, when they are completed, and take the form of either a `Tap` or a `Swipe`:  
> `namedtuple("Tap", ['x', 'y', 'size', 'duration'])`  
> `namedtuple("Swipe", ['x0', 'y0', 'x1', 'y1', 'size', 'duration', 'distance', 'direction'])`
> <br />
<br />
