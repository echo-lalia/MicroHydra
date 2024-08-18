
### keyboard
[keyboard.py](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/main/MicroHydra/lib/keyboard.py) makes it easy to get button inputs from the keyboard matrix on the Cardputer. To use it, you import it with:   
```from lib import keyboard```

Then, you can access the pressed keys like this:
``` Python
kb = keyboard.KeyBoard() # init the object controlling our keyboard

# return a list of keys that are newly pressed (not keys that were already pressed)
keys = kb.get_new_keys()

# if you would also like to check for a specific key being held (for example, checking for key combinations), 
# you can do something like this:
if "CTL" in kb.key_state:
    print("Control!")
```   

If you'd like to process key presses manually, you can also just use something like this:
``` Python
# get a list of keys that are currently pressed down
pressed_keys = kb.get_pressed_keys()
```

And that's it! It even automatically applies the 'shift' and 'fn' keys for you, so it's very quick and easy to work with.   
Take a look at the keymaps at the top of lib/keyboard.py if you want to see all the possible key values. 

<br />

<br />

*One more note on the keyboard library; I named the key on the top of the device "GO" instead of "G0" because I thought it was cute. Now that people are actually using my library I'm feeling a little silly for this choice, as I worry it might confuse some developers. That said, I also don't want to change it because it would be a breaking change, and it doesn't really harm anyone otherwise. So, figure I'll just make a note here to help prevent confusion instead.*
