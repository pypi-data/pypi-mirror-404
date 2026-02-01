from typing import Union, Optional, Literal
from pathlib import Path
from pathlike_typing import PathLike
from hrenpack.classes import range_plus


def literal_add(base, *args):
    return Union[base, Literal[*args]]


Number = Union[int, float]
SimpleList = Union[list, tuple, set]
si = Union[int, str]
IntStr = si
NullStr = Optional[str]
integer, string, boolean = int, str, bool
ColorTyping = Union[tuple[int, int, int], list[int, int, int], tuple[int, int, int, float], list[int, int, int, float]]
FivePointScale = Literal[*range_plus(5)]
TenPointScale = Literal[*range_plus(10)]
ZeroFivePointScale = literal_add(FivePointScale, 0)
ZeroTenPointScale = literal_add(TenPointScale, 0)
