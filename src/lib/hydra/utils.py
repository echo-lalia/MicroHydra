"""Common utilities for MicroHydra core modules."""


def clamp(x: float, minimum: float, maximum: float) -> int|float:
    """Clamp the given value to the range `minimum` - `maximum`.

    This function is faster than using `min(max(val, val), val)`
    (in my testing, at least), and a bit more readable, too.
    """
    if x < minimum:
        return minimum
    if x > maximum:
        return maximum
    return x


def get_instance(cls, *, allow_init: bool = True) -> object:
    """Get the active instance of the given class.

    If an instance doesn't exist and `allow_init` is `True`, one will be created and returned.
    Otherwise, if there is no instance, raises `AttributeError`.
    """
    if hasattr(cls, 'instance'):
        return cls.instance
    if allow_init:
        return cls()
    msg = f"{cls.__name__} has no instance. (You must initialize it first)"
    raise AttributeError(msg)
