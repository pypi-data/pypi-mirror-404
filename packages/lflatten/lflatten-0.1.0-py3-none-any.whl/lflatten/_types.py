type Primitive = bool | int | float | str | None
type Iter = dict | list
type Data = Iter | Primitive
type Flatten = dict[str, Primitive]
type UnFlatten = dict[str, Data]

from typing import overload