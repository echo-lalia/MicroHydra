import machine
try:
    from . import st7789
except:
    from lib.display import st7789


_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)


class Display(st7789.ST7789):
    def __new__(cls, **kwargs):
        if not hasattr(cls, 'instance'):
          cls.instance = super(Display, cls).__new__(cls)
        return cls.instance
    
    def __init__(self, use_tiny_buf=False, **kwargs):
        super().__init__(
            machine.SPI(
                1,
                baudrate=40000000,
                sck=machine.Pin(36),
                mosi=machine.Pin(35),
                miso=None
                ),
            _DISPLAY_HEIGHT,
            _DISPLAY_WIDTH,
            reset=machine.Pin(33, machine.Pin.OUT),
            cs=machine.Pin(37, machine.Pin.OUT),
            dc=machine.Pin(34, machine.Pin.OUT),
            backlight=machine.Pin(38, machine.Pin.OUT),
            rotation=1,
            color_order=st7789.BGR,
            use_tiny_buf=use_tiny_buf,
            **kwargs,
            )
    
    def show(self):
        super().show()
