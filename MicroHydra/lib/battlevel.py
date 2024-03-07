import machine



# CONSTANTS:
# vbat has a voltage divider of 1/2
_MIN_VALUE = const(1575000) # 3.15v
_MAX_VALUE = const(2100000) # 4.2v

_LOW_THRESH = const(_MIN_VALUE + ((_MAX_VALUE - _MIN_VALUE) // 3))
_HIGH_THRESH = const(_LOW_THRESH + ((_MAX_VALUE - _MIN_VALUE) // 3))



# CLASS Battery:
class Battery:
    def __init__(self):
        #init the ADC for the battery
        self.adc = machine.ADC(10)
        self.adc.atten(machine.ADC.ATTN_11DB) # needed to get apropriate range
        
    def read_pct(self):
        """
        Return an approximate battery level as a percentage
        """
        raw_value = self.adc.read_uv()
    
        if raw_value <= _MIN_VALUE:
            return 0
        elif raw_value >= _MAX_VALUE:
            return 100
        
        delta_value = raw_value - _MIN_VALUE # shift range down
        delta_max = _MAX_VALUE - _MIN_VALUE # shift range down
        pct_value = int((delta_value / delta_max) * 100)
        return (pct_value)

    def read_level(self):
        """
        Read approx battery level on the adc and return as int range 0 (low) to 3 (high)
        This is reccomended, as the readings are not very accurate,
        and a percentage could therefore be misleading.
        """
        raw_value = self.adc.read_uv()
        if raw_value < _MIN_VALUE:
            return 0
        if raw_value < _LOW_THRESH:
            return 1
        if raw_value < _HIGH_THRESH:
            return 2
        return 3

if __name__ == "__main__":
    from lib import st7789fbuf, keyboard
    from lib import microhydra as mh
    from launcher.icons import battery
    import time
    from font import vga2_16x32 as font
    from machine import SPI, Pin, PWM, reset, ADC
    
    tft = st7789fbuf.ST7789(
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
    batt = Battery()
    
    while True:
        time.sleep(1)
        tft.fill(0)
        tft.bitmap_text(font, f"Batt level: {batt.read_level()}", 10,10, 65535)
        tft.bitmap_text(font, f"pct: {batt.read_pct()}%", 10,50, 65535)
        tft.show()

