"""Back easing functions.

All of these functions take and return a float from 0.0 to 1.0
and are based on Penner's easing functions,
and easings.net
"""

_C1 = const(1.70158)
_C2 = const(2.594909)
_C3 = const(2.70158)


def ease_in_back(x: float) -> float:
    """Apply ease in function to the given float."""
    return _C3*x*x*x - _C1*x*x


def ease_out_back(x: float) -> float:
    """Apply ease out function to the given float."""
    return 1 + _C3 * (x - 1)**3 + _C1 * (x - 1)**2


def ease_in_out_back(x: float) -> float:
    """Apply ease in/out function to the given float."""
    return (
        ((2 * x)**2 * ((_C2 + 1)*2*x - _C2)) / 2
        if x < 0.5 else
        ((2*x - 2)**2 * ((_C2 + 1) * (x*2 - 2) + _C2) + 2) / 2
    )
