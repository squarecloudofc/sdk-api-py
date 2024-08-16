from .constants import USING_PYDANTIC

if USING_PYDANTIC:
    from pydantic import ConfigDict, validate_call


def validate(func: callable) -> callable:
    if USING_PYDANTIC:
        return validate_call(
            func, config=ConfigDict(arbitrary_types_allowed=True)
        )
    return func
