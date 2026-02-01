import dataclasses
from dataclasses import Field, field

from typing import Any


def env_field(env_var: str, *, default: Any = dataclasses.MISSING) -> Field:
    """Creates a field that loads its value from a single environment variable."""
    metadata = {"env": env_var}
    if default is not dataclasses.MISSING:
        return field(default=default, metadata=metadata)
    return field(metadata=metadata)


def prefix_field(prefix: str) -> Field:
    """Creates a nested config field that uses the given string as a prefix."""
    # This field must be a dataclass, so it doesn't need a default value here.
    # The loader will instantiate it.
    return field(metadata={"prefix": prefix})



