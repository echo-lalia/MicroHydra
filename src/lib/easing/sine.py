"""Sine easing functions.

All of these functions take and return a float from 0.0 to 1.0
and are based on Penner's easing functions,
and easings.net
"""
import math


def ease_in_sine(x: float) -> float:
    """Apply ease in function to the given float."""
    return 1 - math.cos((x * math.pi) / 2)


def ease_out_sine(x: float) -> float:
    """Apply ease out function to the given float."""
    return math.sin((x * math.pi) / 2)


def ease_in_out_sine(x: float) -> float:
    """Apply ease in/out function to the given float."""
    return -(math.cos(math.pi * x) - 1) / 2
