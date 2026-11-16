"""Base classes of the method groups and the async descriptor."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, Concatenate, Generic, ParamSpec, TypeVar

if TYPE_CHECKING:
    from .client import SquareCloud


class _Group:
    def __init__(self, client: SquareCloud) -> None:
        self._c = client


P = ParamSpec('P')
R = TypeVar('R')


class _aio(Generic[P, R]):
    """Expose a sync method as a coroutine that runs in ``asyncio.to_thread``."""

    def __init__(self, fn: Callable[Concatenate[Any, P], R]) -> None:
        self._fn = fn
        self.__doc__ = fn.__doc__

    def __get__(
        self, obj: Any, owner: type | None = None
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        if obj is None:  # Class access, as by help() or inspect.
            return self  # type: ignore[return-value]
        fn, sync = self._fn, obj._sync

        async def call(*args: P.args, **kwargs: P.kwargs) -> R:
            import asyncio

            return await asyncio.to_thread(fn, sync, *args, **kwargs)

        call.__doc__ = self.__doc__  # Hover and help() show the sync docstring.
        return call


class _AsyncGroup:
    def __init__(self, sync: Any) -> None:
        self._sync = sync
