"""This Module provides an easy to use Display object for creating graphics in MicroHydra."""

import machine

from . import st7789


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
    """Main graphics class for MicroHydra.

    Subclasses the device-specific display driver.
    """

    # Set to True to redraw all overlays next time show is called
    draw_overlays = False
    # A public list of overlay functions, to be called in order.
    overlay_callbacks = []

    def __new__(cls, **kwargs):  # noqa: ARG003, D102
        if not hasattr(cls, 'instance'):
          Display.instance = super().__new__(cls)
        return cls.instance


    def __init__(
            self,
            *,
            use_tiny_buf=False,
            **kwargs):
        """Initialize the Display."""
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
        Display.draw_overlays = True  # Draw all overlays once on the first show()


    @staticmethod
    def _init_pin(target_pin, *args) -> machine.Pin|None:
        """For __init__: return a pin if an integer is given, or return None."""
        if target_pin is None:
            return None
        return machine.Pin(target_pin, *args)


    def _draw_overlays(self):
        """Call each overlay callback in Display.overlay_callbacks."""
        for callback in Display.overlay_callbacks:
            callback(self)


    def show(self):
        """Write changes to display."""
        if Display.draw_overlays:
            self._draw_overlays()
            Display.draw_overlays = False
        super().show()
