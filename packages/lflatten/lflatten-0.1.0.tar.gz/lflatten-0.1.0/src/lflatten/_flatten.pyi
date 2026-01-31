from typing import Any

from ._types import Flatten

def flatten(
    data: Any,
    sep: str = ".",
    *,
    prefix: str = "",
    ignore_none: bool = True,
) -> Flatten: 
    """Flattens a data structure.

```
data = {
    "foo": {
        "bar": "Hello!"
    }
}
fdata = flatten(data)
print(fdata)
# {"foo.bar": "Hello!"}

```

    Args:
        data (Any): Data structure
        sep (str, optional): Path separator. Defaults to ".".
        prefix (str, optional): Key prefix. Defaults to "".
        ignore_none (bool, optional): Ignores `None` values. Defaults to True.

    Returns:
        Flatten: Flatten data structure, `dict[str, PRIMITIVE]`
    """
    ...