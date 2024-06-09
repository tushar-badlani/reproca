from collections.abc import Awaitable, Callable
from inspect import signature
from types import UnionType
from typing import Any, get_origin, get_type_hints

import msgspec


class Method(msgspec.Struct):
    implementation: Any
    type: type[msgspec.Struct]
    decoder: msgspec.json.Decoder[Any]
    type_hints: dict[str, Any]
    parameter_session_optional: bool
    rate_limit: int = 0


methods: dict[str, Method] = {}


def snake_to_pascal(snake: str) -> str:
    """Convert `snake_case` to `PascalCase`."""
    return "".join(word.capitalize() for word in snake.split("_"))


SPECIAL_PARAMETERS = ["return", "session", "credentials"]


def method[**P, R](func: Callable[P, Awaitable[R]], rate_limit : int) -> Callable[P, Awaitable[R]]:
    type_hints = get_type_hints(func)
    type_ = msgspec.defstruct(
        snake_to_pascal(func.__name__) + "Parameters",
        (
            (key, type_hints[value.name])
            if value.default is value.empty
            else (key, type_hints[value.name], value.default)
            for key, value in signature(func).parameters.items()
            if key not in SPECIAL_PARAMETERS
        ),
    )
    parameter_session_optional = False
    if (obj := type_hints.get("session")) and get_origin(obj) is UnionType:
        parameter_session_optional = True

    # Add rate_limit to Method object
    methods[f"/{func.__name__}"] = Method(
        implementation=func,
        type=type_,
        decoder=msgspec.json.Decoder(type=type_),
        type_hints=type_hints,
        parameter_session_optional=parameter_session_optional,
        rate_limit=rate_limit,
    )
    return func
