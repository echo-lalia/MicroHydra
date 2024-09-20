"""Quad easing functions.

All of these functions take and return a float from 0.0 to 1.0
and are based on Penner's easing functions,
and easings.net
"""


def ease_in_quad(x: float) -> float:
    """Apply ease in function to the given float."""
    return x * x


def ease_out_quad(x: float) -> float:
    """Apply ease out function to the given float."""
    return 1 - (1 - x) * (1 - x)


def ease_in_out_quad(x: float) -> float:
    """Apply ease in/out function to the given float."""
    return (
        2 * x * x
        if x < 0.5 else
        1 - (-2*x + 2)**2 / 2
    )
