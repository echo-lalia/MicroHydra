import machine
try:
    from . import st7789
except:
    from lib.display import st7789

# ~~~~~ Magic constants:
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)

_MH_DISPLAY_SPI_ID = const(1)
_MH_DISPLAY_BAUDRATE = const(40_000_000)
_MH_DISPLAY_SCK = const(36)
_MH_DISPLAY_MOSI = const(35)
_MH_DISPLAY_MISO = const(None)
_MH_DISPLAY_RESET = const(33)
_MH_DISPLAY_CS = const(37)
_MH_DISPLAY_DC = const(34)
_MH_DISPLAY_BACKLIGHT = const(38) 
_MH_DISPLAY_ROTATION = const(1)


class Display(st7789.ST7789):

    overlay_callbacks = []

    def __new__(cls, **kwargs):
        if not hasattr(cls, 'instance'):
          cls.instance = super(Display, cls).__new__(cls)
        return cls.instance


    def __init__(self, use_tiny_buf=False, **kwargs):
        # mh_if TDECK:
        # # Enable Peripherals:
        # machine.Pin(10, machine.Pin.OUT, value=1)
        # mh_end_if

        if hasattr(self, 'fbuf'):
            print("WARNING: Display re-initialized.")
        super().__init__(
            machine.SPI(
                _MH_DISPLAY_SPI_ID,
                baudrate=_MH_DISPLAY_BAUDRATE,
                sck=machine.Pin(_MH_DISPLAY_SCK),
                mosi=machine.Pin(_MH_DISPLAY_MOSI),
                miso=self._init_pin(_MH_DISPLAY_MISO),
                ),
            _MH_DISPLAY_HEIGHT,
            _MH_DISPLAY_WIDTH,
            reset=self._init_pin(_MH_DISPLAY_RESET, machine.Pin.OUT),
            cs=machine.Pin(_MH_DISPLAY_CS, machine.Pin.OUT),
            dc=machine.Pin(_MH_DISPLAY_DC, machine.Pin.OUT),
            backlight=machine.Pin(_MH_DISPLAY_BACKLIGHT, machine.Pin.OUT),
            rotation=_MH_DISPLAY_ROTATION,
            color_order="BGR",
            use_tiny_buf=use_tiny_buf,
            **kwargs,
            )


    @staticmethod
    def _init_pin(target_pin, *args):
        """For __init__: return a pin if an integer is given, or return None."""
        if target_pin is None:
            return
        return machine.Pin(target_pin, *args)


    def _draw_overlays(self):
        """Call each overlay callback in Display.overlay_callbacks"""
        for callback in Display.overlay_callbacks:
            callback(self)
        

    def show(self):
        self._draw_overlays()
        super().show()
