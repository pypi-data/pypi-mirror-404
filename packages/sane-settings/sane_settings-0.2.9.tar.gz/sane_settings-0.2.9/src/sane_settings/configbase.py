import os
import types
import typing
from typing import Any, TypeVar
import dataclasses
from dataclasses import dataclass
from pprint import pprint

from loguru import logger
from .exceptions import MissingEnvVarError, InvalidTypeError


T = TypeVar("T")


def _cast_var(
    ftype: Any, name: str, raw_value: Any, config_kwargs: dict, full_env_var_name: str
):
    try:
        if ftype is bool:
            if isinstance(raw_value, bool):
                config_kwargs[name] = raw_value
            else:
                match str(raw_value).lower():
                    case "true" | "1" | "t" | "yes":
                        config_kwargs[name] = True
                    case "false" | "0" | "f" | "no":
                        config_kwargs[name] = False
                    case _:
                        raise InvalidTypeError(
                            f"Failed to cast env var '{full_env_var_name}' (value: '{raw_value}') to type {ftype.__name__} for attribute '{name}'."
                        )
        elif typing.get_origin(ftype) is typing.Literal:
            if raw_value in typing.get_args(ftype):
                config_kwargs[name] = raw_value
            else:
                raise InvalidTypeError(
                    f"Failed to cast env var '{full_env_var_name}' (value: '{raw_value}') to Literral for attribute '{name}'. Allowed values are {','.join(typing.get_args(ftype))}"
                )
        elif typing.get_origin(ftype) in (types.UnionType, typing.Union):
            union_types = typing.get_args(ftype)
            if len(union_types) == 2 and types.NoneType in union_types:
                if raw_value in ("None", "none", None):
                    logger.debug(f"field {name} detected as none")
                    config_kwargs[name] = None
                else:
                    non_none_type = next(t for t in union_types if t is not type(None))
                    config_kwargs = _cast_var(
                        non_none_type, name, raw_value, config_kwargs, full_env_var_name
                    )
            else:
                raise InvalidTypeError(
                    f"'{name}' is invalid. Union type is only allowed for exactly 2 types, one of both being None"
                )
        else:
            config_kwargs[name] = ftype(raw_value)
    except (ValueError, TypeError) as exc:
        raise InvalidTypeError(
            f"Failed to cast env var '{full_env_var_name}' (value from env var: '{raw_value}') to type {ftype.__name__} for attribute '{name}'. | {str(exc)} "
        )

    return config_kwargs


@dataclass
class EnvConfigBase:
    @classmethod
    def load_from_env(
        cls: type[T],
        _prefix: str = "",
        _separator: str = "__",
        pretty_check: bool = False,
        app_prefix: str = "",
    ) -> T:
        config_kwargs = {}
        # Apply app_prefix if provided
        if app_prefix:
            _prefix = f"{app_prefix}{_separator}{_prefix}" if _prefix else app_prefix

        for f in dataclasses.fields(cls):
            # 1. Check for a nested prefix field first
            nested_prefix = f.metadata.get("prefix")
            if nested_prefix:
                # Construct the full prefix for the recursive call
                full_prefix = (
                    f"{_prefix}{_separator}{nested_prefix}"
                    if _prefix
                    else nested_prefix
                )

                # Handle Union types (like Optional[SomeConfig])
                if typing.get_origin(f.type) in (types.UnionType, typing.Union):
                    union_types = typing.get_args(f.type)
                    if len(union_types) == 2 and types.NoneType in union_types:
                        # Check if the prefix exists in environment variables
                        non_none_type = next(
                            t for t in union_types if t is not type(None)
                        )
                        # Check if any env var with this prefix exists
                        prefix_exists = any(
                            key.startswith(full_prefix + _separator)
                            for key in os.environ.keys()
                        )
                        if prefix_exists:
                            config_kwargs[f.name] = non_none_type.load_from_env(
                                _prefix=full_prefix, app_prefix=""
                            )
                        else:
                            config_kwargs[f.name] = None
                    else:
                        raise InvalidTypeError(
                            f"'{f.name}' is invalid. Union type is only allowed for exactly 2 types, one of both being None"
                        )
                else:
                    # Recursively load the nested model with the new prefix
                    config_kwargs[f.name] = f.type.load_from_env(
                        _prefix=full_prefix, app_prefix=""
                    )
                continue

            # 2. Check for a direct environment variable field
            env_var_name_part = f.metadata.get("env")
            if env_var_name_part:
                full_env_var_name = (
                    f"{_prefix}{_separator}{env_var_name_part}"
                    if _prefix
                    else env_var_name_part
                )
                # The rest of the value-loading logic is the same as before...
                raw_value = os.getenv(full_env_var_name)
                if raw_value is None:
                    if f.default != dataclasses.MISSING:
                        config_kwargs = _cast_var(
                            f.type, f.name, f.default, config_kwargs, full_env_var_name
                        )
                        logger.debug(
                            f"field {f.name} loading from {full_env_var_name} used its default value"
                        )
                    else:
                        raise MissingEnvVarError(full_env_var_name, f.name)
                else:
                    config_kwargs = _cast_var(
                        f.type, f.name, raw_value, config_kwargs, full_env_var_name
                    )

        retval = cls(**config_kwargs)
        if pretty_check:
            pprint(retval)

        return retval
