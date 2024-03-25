from lib import st7789fbuf, keyboard, mhconfig, HydraMenu
from machine import Pin, SPI
from font import vga2_16x32 as font
import time, machine

# make the animations smooth :)
machine.freq(240_000_000)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Globals: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
kb = keyboard.KeyBoard()
keys = kb.get_new_keys()
config = mhconfig.Config()

display = st7789fbuf.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
    )

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def update_config(caller, value):
    config[caller.text] = value
    config.generate_palette()
    print(f"config['{caller.text}'] = {value}")

def discard_conf(caller):
    print("Discard config.")
    display.fill(0)
    display.show()
    time.sleep_ms(10)
    machine.reset()

def save_conf(caller):
    config.save()
    print("Save config: ", config.config)
    display.fill(0)
    display.show()
    time.sleep_ms(10)
    machine.reset()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Key Repeater: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_KEY_HOLD_MS = const(600)
_KEY_REPEAT_MS = const(80)
_KEY_REPEAT_DELTA = const(_KEY_HOLD_MS - _KEY_REPEAT_MS)

class KeyRepeater:
    """
    KeyRepeater tracks the time since a key was pressed, and repeats keypresses at a specified interval.
    """
    def __init__(self):
        self.tracker = {}
        
    def update_keys(self, keylist):
        tracked_keys = self.tracker.keys()
        time_now = time.ticks_ms()
                
        # add new keys to tracker
        for key in keylist:
            if key not in tracked_keys:
                self.tracker[key] = time.ticks_ms()
        
        
        for key in tracked_keys:
            # remove keys that arent being pressed from tracker
            if key not in kb.key_state:
                self.tracker.pop(key)
            
            # test if keys have been held long enough to repeat
            elif time.ticks_diff(time_now, self.tracker[key]) >= _KEY_HOLD_MS:
                keylist.append(key)
                self.tracker[key] = time.ticks_ms() - _KEY_REPEAT_DELTA
        
        return keylist

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main body: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Thanks to HydraMenu, the settings app is now pretty small.
# So, not much point in overcomplicating things:

menu = HydraMenu.Menu(display_fbuf=display, config=config, font=font, esc_callback=discard_conf)

menu_def = [
    (HydraMenu.IntItem, 'volume', {'min_int':0,'max_int':10, 'instant_callback':update_config}),
    (HydraMenu.RGBItem, 'ui_color', {'instant_callback':update_config}),
    (HydraMenu.RGBItem, 'bg_color', {'instant_callback':update_config}),
    (HydraMenu.WriteItem, 'wifi_ssid', {}),
    (HydraMenu.WriteItem, 'wifi_pass', {'hide':True}),
    (HydraMenu.BoolItem, 'sync_clock', {}),
    (HydraMenu.IntItem, 'timezone', {'min_int':-13,'max_int':13}),
    ]

# build menu from def
for i_class, name, kwargs in menu_def:
    menu.append(
        i_class(
            menu,
            name,
            config[name],
            callback=update_config,
            **kwargs
            ))
menu.append(HydraMenu.DoItem(menu, "Confirm", callback=save_conf))

repeater = KeyRepeater()

updating_display = True

while True:
    keys = kb.get_new_keys()
    
    keys = repeater.update_keys(keys)
    
    for key in keys:
        menu.handle_input(key)
    
    if keys:
        updating_display = True
        
    if updating_display:
        updating_display = menu.draw()
        display.show()
    
    
    if not keys and not updating_display:
        time.sleep_ms(1)
