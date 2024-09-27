"""Circ easing functions.

All of these functions take and return a float from 0.0 to 1.0
and are based on Penner's easing functions,
and easings.net
"""
import math


def ease_in_circ(x: float) -> float:
    """Apply ease in function to the given float."""
    return 1 - math.sqrt(1 - x**2)


def ease_out_circ(x: float) -> float:
    """Apply ease out function to the given float."""
    return math.sqrt(1 - (x - 1)**2)


def ease_in_out_circ(x: float) -> float:
    """Apply ease in/out function to the given float."""
    return (
        (1 - math.sqrt(1 - (2*x)**2)) / 2
        if x < 0.5 else
        (math.sqrt(1 - (-2*x + 2)**2) + 1) / 2
    )
