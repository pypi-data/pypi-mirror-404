from typing import Any
from ._types import Flatten


def _split_escaped(key: str, sep: str) -> list[str]:
    parts: list[str] = []
    buf = []
    i = 0

    while i < len(key):
        c = key[i]

        if c == "\\":
            i += 1
            if i < len(key):
                buf.append(key[i])
        elif key.startswith(sep, i):
            parts.append("".join(buf))
            buf.clear()
            i += len(sep) - 1
        else:
            buf.append(c)

        i += 1

    parts.append("".join(buf))
    return parts


def unflatten(data: Flatten, sep: str = ".") -> dict[str, Any]:
    """Unflattens a flattened data strucutre.

    
```
fdata = {"foo.bar": "Hello!"}
data = unflatten(data)
print(data)
#   {
#       "foo": {
#           "bar": "Hello!"
#       }
#   }
```

    Args:
        data (Flatten): Flattened data structutre
        sep (str, optional): Separator. Defaults to ".".

    Returns:
        dict[str, Any]: Unflattened data structure
    """
    out: dict[str, Any] = {}

    for flat_key, value in data.items():
        keys = _split_escaped(flat_key, sep)
        cur: Any = out

        for i, k in enumerate(keys):
            is_last = i == len(keys) - 1
            is_index = k.isdigit()
            key: Any = int(k) if is_index else k

            if is_last:
                if isinstance(cur, list):
                    while len(cur) <= key:
                        cur.append(None)
                    cur[key] = value
                else:
                    cur[key] = value
                continue

            if isinstance(cur, list):
                while len(cur) <= key:
                    cur.append(None)
                if cur[key] is None:
                    cur[key] = [] if keys[i + 1].isdigit() else {}
                cur = cur[key]
            else:
                if key not in cur:
                    cur[key] = [] if keys[i + 1].isdigit() else {}
                cur = cur[key]

    return out
