[HydraMenu.py](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/main/src/lib/hydra/menu.py) is a module contributed by [Gabriel-F-Sousa](https://github.com/echo-lalia/Cardputer-MicroHydra/commits?author=Gabriel-F-Sousa), which is designed to make it easy to create menu screens for MicroHydra apps.

HydraMenu is being utilized heavily by the (newly refurbished) inbuilt [settings app](https://github.com/echo-lalia/Cardputer-MicroHydra/blob/main/src/launcher/settings.py). Please take a look at that file for some practical examples of what can be done with the module. 

Here's a simplified example, for your reference:
``` Python
from lib.display import Display
from lib.userinput import UserInput
from lib.hydra.config import Config
from lib.hydra import menu as HydraMenu

# ...
userinput = UserInput()
display = Display()
config = Config()
# ...


""" Create our HydraMenu.Menu:
"""
menu = HydraMenu.Menu()


"""Add menu items to the menu:
"""

# this is an integer menu item:
menu.append(HydraMenu.IntItem(
    # items should be passed their parent menu, and they can be given display text.
    menu=menu, text="IntItem",
    # Items can be given a value as well. For an IntItem, this value should be an int
    value=5,
    # some MenuItems also have special keywords that can be used for further options.
    # int items, for example, can be given a minimum and maximum value.
    min_int=0, max_int=10,
    # callbacks are what makes this all functional.
    # Pass the function you want to be called every time a value is confirmed. 
    callback=lambda item, val: print(f"Confirmed val: {val}"),
    # You can also use an 'instant_callback' if you want to track the value as it changes.
    # this is what the main settings app uses to update the volume, and ui colors as they're changed.
    instant_callback=lambda item, val: print(val)
    ))

...

# create a variable to remember/decide when we need to redraw the menu:
redraw = True

# this loop will run our menu's logic.
while True:
    
    # get our newly pressed keys
    keys = userinput.get_new_keys()
    
    # pass each key to the handle_input method of our menu.
    for key in keys:
        menu.handle_input(key)
    
    
    # when any key is pressed, we must redraw:
    if keys:
        redraw = True
    
    # this is used to prevent unneeded redraws (and speed up the app)
    # just calling menu.draw and display.show every loop also works, but it feels slower.
    if redraw:
        # menu.draw returns True when it is mid-animation,
        # and False when the animation is done (therefore, does not need to be redrawn until another key is pressed)
        redraw = menu.draw()
        display.show()  

```
