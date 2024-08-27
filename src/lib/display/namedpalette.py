"""
This module is intended to be a helpful, and optional, companion for lib.display.pallete,
for reference and convenience.
"""

from .palette import Palette

# Palette class
class NamedPalette:
    names = {
        'black':0,
        'bg_dark':1,
        'bg_color':2,
        'mid_color':5,
        'ui_color':8,
        'ui_light':9,
        'white':10,
        'red':11,
        'green':12,
        'blue':13,
        'bg_complement':14,
        'ui_complement':15,
    }
    def __init__(self):
        self.palette = Palette.instance if hasattr(Palette, 'instance') else Palette()

    @staticmethod
    def _str_to_idx(val:str|int) -> int:
        if isinstance(val, str):
            return NamedPalette.names(
                val.lower()
            )
        return val

    def __len__(self) -> int:
        return len(self.palette)

    def __setitem__(self, key:int|str, new_val:int):
        self.palette[self._str_to_idx(key)] = new_val

    def __getitem__(self, key:int|str) -> int:
        return self.palette[self._str_to_idx(key)]
    
    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
