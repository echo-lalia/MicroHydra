from lib import st7789fbuf, keyboard, mhconfig, HydraMenu
from machine import Pin, SPI, PWM
from font import vga1_8x16 as small_font
from font import vga2_16x32 as font
from lib import microhydra as mh

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

menu = HydraMenu.Menu(display_fbuf=display, font=font)

r,g,b = mh.separate_color565(config["bg_color"])
bg_rgb = [r,g,b]
r,g,b = mh.separate_color565(config["ui_color"])
ui_rgb = [r,g,b]

def rgb_change(caller, color):
    if caller.text == "ui_color":
        config["ui_color"] = color
    if caller.text == "bg_color":
        config["bg_color"] = color
    print(caller.text, color)

def sync_clock(caller, BOOL):
    config["sync_clock"] = BOOL
    print(caller.text, BOOL)

def change_vol(caller, numb):
    config["volume"] = numb
    print(caller.text, numb)
    
def change_ssd(caller, text):
    config["wifi_ssid"] = text
    print(caller.text, text)
    
def change_wifi_pass(caller, text):
    config["wifi_pass"] = text
    print(caller.text, text)

def change_timezone(caller, numb):
    config["timezone"] = numb
    print(caller.text, numb)

def save_conf(caller):
    config.save()
    print("save config: ", config)

menu.append(HydraMenu.IntItem(menu, "volume", config["volume"], min_int=0, max_int=10, callback=change_vol))
menu.append(HydraMenu.RGBItem(menu, "ui_color", ui_rgb, callback=rgb_change))
menu.append(HydraMenu.RGBItem(menu, "bg_color", bg_rgb, callback=rgb_change))
menu.append(HydraMenu.WriteItem(menu, "wifi_ssid", config["wifi_ssid"], callback=change_ssd))
menu.append(HydraMenu.WriteItem(menu, "wifi_pass", config["wifi_pass"], hide=True, callback=change_wifi_pass))
menu.append(HydraMenu.BoolItem(menu, "sync_clock", config["sync_clock"], callback=sync_clock))
menu.append(HydraMenu.IntItem(menu, "timezone", config["timezone"], min_int=-13, max_int=13, callback=change_timezone))
menu.append(HydraMenu.DoItem(menu, "Confirm", callback=save_conf))

menu.display_menu()

display.show()
while True:
    keys = kb.get_new_keys()
    
    for key in keys:
        menu.handle_input(key)
    
    
    display.show()  
