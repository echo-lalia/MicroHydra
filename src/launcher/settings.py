"""
Builtin Settings app for MicroHydra.
This app provides a useful GUI for changing the values in /config.json
"""

from lib import userinput
from lib.hydra import config
from lib.hydra import menu as hydramenu
from lib.display import Display
from lib.hydra.i18n import I18n
import time
import machine

# make the animations smooth :)
machine.freq(240_000_000)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Globals: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
display = Display()
kb = userinput.UserInput()
config = config.Config()

trs = {
  "language": {"en": "Language", "zh": "语言/Lang", "ja": "言語/Lang"},
  "volume": {"en": "Volume", "zh": "音量", "ja": "音量"},
  "ui_color": {"en": "UI Color", "zh": "UI颜色", "ja": "UIの色"},
  "bg_color": {"en": "Background Color", "zh": "背景颜色", "ja": "背景色"},
  "wifi_ssid": {"en": "WiFi SSID", "zh": "WiFi名称", "ja": "WiFi名前"},
  "wifi_pass": {"en": "WiFi Password", "zh": "WiFi密码", "ja": "WiFiパスワード"},
  "sync_clock": {"en": "Sync Clock", "zh": "同步时钟", "ja": "時計同期"},
  "24h_clock": {"en": "24-Hour Clock", "zh": "24小时制", "ja": "24時間制"},
  "timezone": {"en": "Timezone", "zh": "时区", "ja": "タイムゾーン"},
  "Confirm": {"en": "Confirm", "zh": "确认", "ja": "確認"}
}


I18N = I18n(trs)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def update_config(caller, value):
    #Find the original ID
    org_id = "language"
    for k,v in trs.items():
        if v[config['language']] == caller.text:
            org_id = k
            break

    config[org_id] = value
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


# mh_if touchscreen:
_MH_DISPLAY_WIDTH = const(320)
_MH_DISPLAY_HEIGHT = const(240)

_CONFIRM_MIN_X = const(_MH_DISPLAY_WIDTH // 4)
_CONFIRM_MAX_X = const(_MH_DISPLAY_WIDTH - _CONFIRM_MIN_X)
_CONFIRM_MIN_Y = const(_MH_DISPLAY_HEIGHT // 4)
_CONFIRM_MAX_Y = const(_MH_DISPLAY_HEIGHT - _CONFIRM_MIN_Y)

def process_touch(keys):
    events = kb.get_touch_events()
    for event in events:
        if hasattr(event, 'direction'):
            # is a swipe
            keys.append(event.direction)
        
        elif _CONFIRM_MIN_X < event.x < _CONFIRM_MAX_X \
        and _CONFIRM_MIN_Y < event.y < _CONFIRM_MAX_Y:
            keys.append("ENT")
# mh_end_if


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main body: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Thanks to HydraMenu, the settings app is now pretty small.
# So, not much point in overcomplicating things:


menu = hydramenu.Menu(
    esc_callback=discard_conf
    )

menu_def = [
    (hydramenu.WriteItem, 'language', {}),
    (hydramenu.IntItem, 'volume', {
     'min_int': 0, 'max_int': 10, 'instant_callback': update_config}),
    (hydramenu.RGBItem, 'ui_color', {'instant_callback': update_config}),
    (hydramenu.RGBItem, 'bg_color', {'instant_callback': update_config}),
    (hydramenu.WriteItem, 'wifi_ssid', {}),
    (hydramenu.WriteItem, 'wifi_pass', {'hide': True}),
    (hydramenu.BoolItem, 'sync_clock', {}),
    (hydramenu.BoolItem, '24h_clock', {}),
    (hydramenu.IntItem, 'timezone', {'min_int': -13, 'max_int': 13}),
]

# build menu from def
for i_class, name, kwargs in menu_def:
    menu.append(
        i_class(
            menu,
            I18N.trans(name),
            config[name],
            callback=update_config,
            **kwargs
        ))
menu.append(hydramenu.DoItem(menu, I18N.trans("Confirm"), callback=save_conf))

updating_display = True


while True:
    keys = kb.get_new_keys()
    
    # mh_if touchscreen:
    process_touch(keys)
    # mh_end_if

    for key in keys:
        menu.handle_input(key)

    if keys:
        updating_display = True

    if updating_display:
        updating_display = menu.draw()
        display.show()

    if not keys and not updating_display:
        time.sleep_ms(1)
