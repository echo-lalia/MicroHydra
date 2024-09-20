"""This very basic module reads the battery ADC values and converts it into a percentage or 0-3 level."""
import machine



# CONSTANTS:
# vbat has a voltage divider of 1/2
_MIN_VALUE = const(1575000) # 3.15v
_MAX_VALUE = const(2100000) # 4.2v

_LOW_THRESH = const(_MIN_VALUE + ((_MAX_VALUE - _MIN_VALUE) // 3))
_HIGH_THRESH = const(_LOW_THRESH + ((_MAX_VALUE - _MIN_VALUE) // 3))

_MH_BATT_ADC = const(10)


# CLASS Battery:
class Battery:
    """Battery info reader."""

    def __init__(self):
        """Create the Battery object."""
        #init the ADC for the battery
        self.adc = machine.ADC(_MH_BATT_ADC)
        self.adc.atten(machine.ADC.ATTN_11DB) # needed to get appropriate range

    def read_pct(self) -> int:
        """Return an approximate battery level as a percentage."""
        raw_value = self.adc.read_uv()

        if raw_value <= _MIN_VALUE:
            return 0
        if raw_value >= _MAX_VALUE:
            return 100

        delta_value = raw_value - _MIN_VALUE # shift range down
        delta_max = _MAX_VALUE - _MIN_VALUE # shift range down
        return int((delta_value / delta_max) * 100)

    def read_level(self) -> int:
        """Read approx battery level on the adc and return as int range 0 (low) to 3 (high)."""
        raw_value = self.adc.read_uv()
        if raw_value < _MIN_VALUE:
            return 0
        if raw_value < _LOW_THRESH:
            return 1
        if raw_value < _HIGH_THRESH:
            return 2
        return 3
