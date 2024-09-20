"""Common utilities for MicroHydra core modules."""

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
