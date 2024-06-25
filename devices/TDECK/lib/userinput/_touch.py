"""
MicroHydra gt911 touchscreen module
Specifically, tailored here for the T-Deck


This module is based on the gt911 driver by esophagoose,
and it has been reworked for MicroHydra.

MIT License

Copyright (c) 2024 esophagoose

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


Original Module Source:
https://github.com/esophagoose/gt911-micropython/
"""

        
import time
from collections import namedtuple
import machine


# TDECK _CONSTANTS:
_BOARD_TOUCH_INT = const(16)
_BOARD_PERIPHERAL_POWER = const(10)

# GT911 _CONSTANTS:
_ADDR1 = const(0x5D)
_ADDR2 = const(0x14)

# DEFAULT TDECK ADDRESS:
_DEFAULT_ADDR = const(_ADDR1)

# Real-time command (Write only)
_COMMAND = const(0x8040)
_ESD_CHECK = const(0x8041)
_COMMAND_CHECK = const(0x8046)

_CONFIG_START = const(0x8047)

_X_OUTPUT_MAX_LOW = const(0x8048)
_X_OUTPUT_MAX_HIGH = const(0x8049)
_Y_OUTPUT_MAX_LOW = const(0x804A)
_Y_OUTPUT_MAX_HIGH = const(0x804B)

_CONFIG_SIZE = const(0xFF - 0x46)

_POINT_INFO = const(0x814E)
_POINT_1 = const(0x814F)

_NUM_POINTS = const(5)


def config_offset(reg: int):
    return reg - _CONFIG_START


@micropython.viper
def minisqrt(n:int) -> int:
    """
    Fast square root for 32 bit integers.
    Adapted directly from wikipedia.org/wiki/Methods_of_computing_square_roots
    """
    x = n
    c = 0
    d = 1 << 28
    
    while d > n:
        d >>= 2

    while d != 0 :
        if x >= c + d:
            x -= c + d
            c = (c >> 1) + d
        else:
            c >>= 1
        
        d >>= 2

    return c



TouchPoint = namedtuple("TouchPoint", ["id", "x", "y", "size"])

Tap = namedtuple("Tap", ['x', 'y', 'size', 'duration'])
Swipe = namedtuple("Swipe", ['x0', 'y0', 'x1', 'y1', 'size', 'duration', 'distance', 'direction'])



class TouchEvent:
    """
    This class handles tracking and related logic for reading touch data.
    """
    swipe_move_thresh=30
    def __init__(self, point=None):
        if point:
            self.alive = True
            _, start_x, start_y, start_size = point
        else:
            self.alive = False
            start_x = 0
            start_y = 0
            start_size = 0
        
        self.start_x = start_x
        self.start_y = start_y
        self.start_size = start_size
        self.start_time = time.ticks_ms()
        
        self.new_x = start_x
        self.new_y = start_y
        self.new_size = start_size


    def track(self, point):
        """Update touchpoint values as it moves"""
        _, new_x, new_y, new_size = point
        self.new_x = new_x
        self.new_y = new_y
        self.new_size = new_size


    @micropython.viper
    def _point_dist(self):
        """
        Calculate movement distance from touch start to end.
        """
        x0 = int(self.start_x)
        y0 = int(self.start_y)
        x1 = int(self.new_x)
        y1 = int(self.new_y)
        
        x = x0 - x1
        y = y0 - y1

        return minisqrt((x*x) + (y*y))


    def _finish_tap(self, touch_time, touch_dist):
        return Tap(
            (self.start_x + self.new_x) // 2,
            (self.start_y + self.new_y) // 2,
            (self.start_size + self.new_size) // 2,
            touch_time,
            )

    
    @micropython.viper
    def _swipe_dir(self):
        x0 = int(self.start_x)
        y0 = int(self.start_y)
        x1 = int(self.new_x)
        y1 = int(self.new_y)
        
        x = x1 - x0
        y = y1 - y0
        
        if abs(x) > abs(y):
            # right or left
            if x > 0:
                return "RIGHT"
            else:
                return "LEFT"
        else:
            # up or down
            if y > 0:
                return "DOWN"
            else:
                return "UP"
        

    def _finish_swipe(self, touch_time, touch_dist):
        return Swipe(
            self.start_x,
            self.start_y,
            self.new_x,
            self.new_y,
            (self.start_size + self.new_size) // 2,
            touch_time,
            touch_dist,
            self._swipe_dir()
            )


    def finish(self):
        """End this event and return collected data"""
        self.alive = False
        touch_time = time.ticks_diff(time.ticks_ms(), self.start_time)
        touch_dist = self._point_dist()
        if touch_dist < TouchEvent.swipe_move_thresh:
            return self._finish_tap(touch_time, touch_dist)

        return self._finish_swipe(touch_time, touch_dist)




class Touch:
    def __init__(self, i2c, interrupt=_BOARD_TOUCH_INT, reset=_BOARD_PERIPHERAL_POWER, rotation=1, swipe_move_thresh=20):
        self.width = 0
        self.height = 0
        self.address = None
        self.configuration = []
        self.i2c = i2c
#         self.i2c =  machine.I2C(1, freq=freq, scl=machine.Pin(scl), sda=machine.Pin(sda))
        self.interrupt = machine.Pin(interrupt, machine.Pin.IN)
        self.reset_pin = machine.Pin(reset, machine.Pin.OUT)

        self.rotation = rotation % 4
        
        TouchEvent.swipe_move_thresh = swipe_move_thresh
        self.tracker = [TouchEvent() for _ in range(_NUM_POINTS)]

        self._begin(_DEFAULT_ADDR)


    @micropython.viper
    def _rotate_xy(self, x:int, y:int):
        """Rotate x/y coordinates such that they align with display coordinates."""
        rotation = int(self.rotation)
        width = int(self.width)
        height = int(self.height)
        
        # if landscape mode:
        if rotation % 2 == 1:
            x, y = y, x
            width, height = height, width
        # invert y
        if rotation == 1 or rotation == 2:
            y = height - y
        # invert x
        if rotation == 2 or rotation == 3:
            x = width - x
            
        return x, y


    def _write(self, reg: int, value: list[int]):
        self.i2c.writeto_mem(self.address, reg, bytes(value), addrsize=16)


    def _read(self, reg: int, length: int):
        data = self.i2c.readfrom_mem(self.address, reg, length, addrsize=16)
        return list(data)


    def enable_interrupt(self, callback):
        self.interrupt.irq(trigger=machine.Pin.IRQ_FALLING, handler=callback)


    def _begin(self, address):
        self.address = address
#         self._reset()
        self.configuration = self._read(_CONFIG_START, _CONFIG_SIZE)
        wl = self.configuration[config_offset(_X_OUTPUT_MAX_LOW)]
        wh = self.configuration[config_offset(_X_OUTPUT_MAX_HIGH)]
        hl = self.configuration[config_offset(_Y_OUTPUT_MAX_LOW)]
        hh = self.configuration[config_offset(_Y_OUTPUT_MAX_HIGH)]
        self.width = (wh << 8) + wl
        self.height = (hh << 8) + hl


#     def _reset(self):
#         self.interrupt.value(0)
#         self.reset_pin.value(0)
#         time.sleep_ms(10)
#         self.interrupt.value(self.address == _ADDR2)
#         time.sleep_ms(1)
#         self.reset_pin.value(1)
#         time.sleep_ms(5)
#         self.interrupt.value(0)
#         time.sleep_ms(50)
#         self.interrupt.init(mode=machine.Pin.IN)
#         time.sleep_ms(50)


    def _parse_point(self, data):
        track_id = data[0]
        x = data[1] + (data[2] << 8)
        y = data[3] + (data[4] << 8)
        x, y = self._rotate_xy(x, y)
        size = data[5] + (data[6] << 8)
        return TouchPoint(track_id, x, y, size)


    def get_touch_events(self):
        """
        Returns a list of Taps or Swipes based on the latest touch data.
        """
        current_points = self.get_current_points()
        active_ids = [point.id for point in current_points]
        tracker = self.tracker
        
        output = []
        
        # add/update touchevents in tracker
        for point in current_points:
            if tracker[point.id].alive:
                # point is already being tracked; update
                tracker[point.id].track(point)
            else:
                # init new touch event in tracker
                tracker[point.id].__init__(point)
        
        # iterate though touchevents to find active events that are finished
        for idx, event in enumerate(tracker):
            if event.alive and idx not in active_ids:
                output.append(event.finish())
        
        return output
                
        


    def get_current_points(self):
        """
        Returns a list of TouchPoints representing the current touch data.
        """
        points = []
        info = self._read(_POINT_INFO, 1)[0]
        ready = bool((info >> 7) & 1)
        # large_touch = bool((info >> 6) & 1)
        touch_count = info & 0xF
        if ready and touch_count > 0:
            for i in range(touch_count):
                data = self._read(_POINT_1 + (i * 8), 7)
                points.append(self._parse_point(data))
        self._write(_POINT_INFO, [0])
        return points




if __name__ == "__main__":
    tp = Touch()

    while True:
        points = tp.get_touch_events()
        if points:
            print(f"Received touch events: {points}")
        time.sleep_ms(10)

