from typing import Union


BASIC_NON_ITERABLE_TYPE = Union[int, float, bool, str]
"""
The basic non iterable type we can accept as
a parameter and that will be transformed into
a `ConstantValue`, including:
- `int`
- `float`
- `bool`
- `str`
"""