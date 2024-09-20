import math


def ease_in_sine(x: float) -> float:
    return 1 - math.cos((x * math.pi) / 2)


def ease_out_sine(x: float) -> float:
    return math.sin((x * math.pi) / 2)


def ease_in_out_sine(x: float) -> float:
    """Apply an easing function to given float."""
    return -(math.cos(math.pi * x) - 1) / 2
