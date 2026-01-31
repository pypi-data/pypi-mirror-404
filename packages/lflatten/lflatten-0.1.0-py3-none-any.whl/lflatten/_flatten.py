from typing import Any

from ._types import Flatten

def _escape(key: str, sep: str) -> str:
    return key.replace("\\", "\\\\").replace(sep, "\\" + sep)

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
    out: dict[str, Any] = {}

    if isinstance(data, dict):
        for k, v in data.items():
            if ignore_none and v is None:
                continue

            k = _escape(str(k), sep)
            new_key = f"{prefix}{sep}{k}" if prefix else k

            if isinstance(v, (dict, list)):
                out.update(
                    flatten(
                        v,
                        sep,
                        prefix=new_key,
                        ignore_none=ignore_none,
                    )
                )
            else:
                out[new_key] = v

    elif isinstance(data, list):
        for i, v in enumerate(data):
            if ignore_none and v is None:
                continue

            k = str(i)
            new_key = f"{prefix}{sep}{k}" if prefix else k

            if isinstance(v, (dict, list)):
                out.update(
                    flatten(
                        v,
                        sep,
                        prefix=new_key,
                        ignore_none=ignore_none,
                    )
                )
            else:
                out[new_key] = v

    else:
        if prefix:
            out[prefix] = data

    return out
