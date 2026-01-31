from typing import Any
from ._types import Flatten

def unflatten(
    data: Flatten, 
    sep: str = "."
) -> dict[str, Any]:
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
    ...