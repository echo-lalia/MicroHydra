"""A reusable statusbar for MicroHydra apps."""

import time

from machine import Timer
from lib.display import Display
from lib.hydra.config import Config
from lib.hydra.utils import get_instance


_MH_DISPLAY_WIDTH = const(240)
_MH_DISPLAY_HEIGHT = const(135)

_STATUSBAR_HEIGHT = const(18)

_SMALL_FONT_HEIGHT = const(8)
_SMALL_FONT_WIDTH = const(8)

_CLOCK_X = const(6)
_CLOCK_Y = const((_STATUSBAR_HEIGHT - _SMALL_FONT_HEIGHT) // 2)
_CLOCK_AMPM_Y = const(_CLOCK_Y - 1)
_CLOCK_AMPM_PADDING = const(2)
_CLOCK_AMPM_X_OFFSET = const(_CLOCK_AMPM_PADDING + _CLOCK_X)

_BATTERY_HEIGHT = const(10)
_BATTERY_X = const(_MH_DISPLAY_WIDTH - 28)
_BATTERY_Y = const((_STATUSBAR_HEIGHT - 10) // 2)



class StatusBar:
    """The MicroHydra statusbar."""

    def __init__(self, *, enable_battery: bool = True, register_overlay: bool = True):
        """Initialize the statusbar."""
        global battery  # noqa: PLW0603

        if enable_battery:
            # If drawing battery status, import battlevel and icons
            from lib import battlevel
            from launcher.icons import battery
            self.batt = battlevel.Battery()

        self.enable_battery = enable_battery

        self.config = get_instance(Config)

        if register_overlay:
            Display.overlay_callbacks.append(self.draw)
            # Set a timer to periodically redraw the clock
            self.timer = Timer(
                # mh_if esp32:
                2,
                # mh_else:
                # -1,
                # mh_end_if
                mode=Timer.PERIODIC,
                period=60_000,
                callback=self._update_overlay,
            )


    @staticmethod
    def _update_overlay(_):
        Display.draw_overlays = True


    @staticmethod
    def _time_24_to_12(hour_24: int, minute: int) -> tuple[str, str]:
        """Convert the given 24 hour time to 12 hour."""
        ampm = 'am'
        if hour_24 >= 12:
            ampm = 'pm'

        hour_12 = hour_24 % 12
        if hour_12 == 0:
            hour_12 = 12

        time_string = f"{hour_12}:{minute:02d}"
        return time_string, ampm


    def draw(self, display: Display):
        """Draw the status bar."""

        # Draw statusbar base
        display.fill_rect(
            0, 0,
            _MH_DISPLAY_WIDTH,
            _STATUSBAR_HEIGHT,
            self.config.palette[4],
        )
        display.hline(
            0, _STATUSBAR_HEIGHT, _MH_DISPLAY_WIDTH,
            self.config.palette[1],
        )

        # clock
        _, _, _, hour_24, minute, _, _, _ = time.localtime()

        if self.config['24h_clock']:
            formatted_time = f"{hour_24}:{minute:02d}"
        else:
            formatted_time, ampm = self._time_24_to_12(hour_24, minute)
            display.text(
                ampm,
                _CLOCK_AMPM_X_OFFSET
                + (len(formatted_time)
                * _SMALL_FONT_WIDTH),
                _CLOCK_AMPM_Y + 1,
                self.config.palette[5],
            )
            display.text(
                ampm,
                _CLOCK_AMPM_X_OFFSET
                + (len(formatted_time)
                    * _SMALL_FONT_WIDTH),
                _CLOCK_AMPM_Y,
                self.config.palette[2],
            )

        display.text(
            formatted_time,
            _CLOCK_X, _CLOCK_Y+1,
            self.config.palette[2],
        )
        display.text(
            formatted_time,
            _CLOCK_X, _CLOCK_Y,
            self.config.palette[7],
        )

        # battery
        if self.enable_battery:
            batt_lvl = self.batt.read_level()
            display.bitmap(
                battery,
                _BATTERY_X,
                _BATTERY_Y,
                index=batt_lvl,
                palette=[self.config.palette[4], self.config.palette[7]],
                )
