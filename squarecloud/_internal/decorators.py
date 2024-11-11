from typing import Any, Callable, TypeVar

from .constants import USING_PYDANTIC

if USING_PYDANTIC:
    from pydantic import ConfigDict, validate_call

F = TypeVar('F', bound=Callable[..., Any])


def validate(func: F) -> Callable[..., Any] | F:
    if USING_PYDANTIC:
        return validate_call(config=ConfigDict(arbitrary_types_allowed=True))(
            func
        )
    return func
