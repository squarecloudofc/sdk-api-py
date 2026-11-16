"""The live feed of an application: :class:`Realtime` and
:class:`AsyncRealtime`."""

from __future__ import annotations

import contextlib
import http.client
import json
import threading
import time
from collections.abc import AsyncIterator, Iterator
from types import TracebackType
from typing import TYPE_CHECKING, Any, cast

from . import _wire
from . import types as t
from ._transport import Response
from .errors import SquareCloudAPIError

if TYPE_CHECKING:
    from .client import SquareCloud

# The API admits one realtime open per user and app every 5 s. The extra
# 0.5 s absorbs clock skew.
_REOPEN_GAP = 5.5


class Realtime:
    """A live feed of an application's events, from :meth:`Apps.realtime`.

    Iterate over it to receive :class:`~squarecloud.types.RealtimeEvent`
    dicts. Every event has ``event``, ``id`` and ``data``, the raw text of
    the event. Log events add ``stream``, which is ``'stdout'`` or
    ``'stderr'``, and the ``line`` itself. Status events add ``status``,
    which always holds the full state, because each partial update is
    merged onto the previous one.

    The connection opens when iteration starts, and the client's
    ``timeout`` applies only until the API answers. If the connection drops,
    or the API asks the client to reconnect, the feed reopens on its own up
    to 3 times in a row, at most once every 5.5 seconds. A ``logs`` or
    ``status`` event resets that count. Iteration ends when the API closes
    the feed, after at most 10 minutes, when it sends
    ``REALTIME_DISCONNECTED``, or when you call :meth:`close`. A connection
    that dies silently, for example when a laptop wakes from sleep, blocks
    until you call :meth:`close` from another thread.

    Use it in a ``with`` block to close it at the end. Each account can
    have up to 5 open feeds, and each application up to 30.

    Raises:
        SquareCloudAPIError: The feed could not be opened, for example 429
            ``REALTIME_MAX_CONNECTIONS`` past 5 open feeds on your account,
            or 429 ``REALTIME_MAX_CONNECTIONS_APP`` past 30 on the
            application. It has the code ``NETWORK_ERROR`` and status 0
            when the feed drops again after 3 reopens in a row.
    """

    def __init__(self, client: SquareCloud, path: str) -> None:
        self._c = client
        self._path = path
        self._resp: Response | None = None
        self._stop = threading.Event()

    def __enter__(self) -> Realtime:
        """Return the feed for use in a ``with`` block."""
        return self

    def __exit__(
        self,
        _type: type[BaseException] | None,
        _value: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        """Close the feed when the ``with`` block ends."""
        self.close()

    def close(self) -> None:
        """Stop the feed, even while it waits to reconnect.

        It is safe to call from another thread.
        """
        self._stop.set()
        if self._resp is not None:
            self._resp.close()

    def __iter__(self) -> Iterator[t.RealtimeEvent]:
        failures = 0  # In a row. A log or status event resets it.
        state: dict[str, Any] = {}
        opened: float | None = None
        stop = self._stop
        while not stop.is_set():
            if opened is not None:  # A reopen backs off, at the API's pace.
                since = time.monotonic() - opened
                _wire._sleep(max(_wire._delay(failures - 1), _REOPEN_GAP - since), stop)
                if stop.is_set():
                    return
            opened = time.monotonic()
            try:
                resp: Response = self._c._request(
                    'GET',
                    self._path,
                    headers={'Accept': 'text/event-stream'},
                    no_timeout=True,
                    stream=True,
                    stop=stop,
                )
            except SquareCloudAPIError:
                if stop.is_set():  # Closed during a retry wait.
                    return
                raise
            self._resp = resp
            if stop.is_set():  # Closed while connecting.
                resp.close()
                return
            reconnect = False
            try:
                for event, text, event_id in _wire._sse(resp):
                    item: dict[str, Any] = {
                        'event': event,
                        'data': text,
                        'id': event_id,
                    }
                    if event == 'logs':
                        failures = 0
                        mark = text[:1]
                        item['stream'] = 'stderr' if mark == '\x02' else 'stdout'
                        item['line'] = text[1:] if mark in ('\x01', '\x02') else text
                    elif event == 'status':
                        failures = 0
                        # A malformed frame keeps the last status.
                        with contextlib.suppress(ValueError, TypeError):
                            state = {**state, **json.loads(text)}
                        item['status'] = state
                    yield cast(t.RealtimeEvent, item)
                    if event == 'system':
                        if text.startswith('REALTIME_DISCONNECTED'):
                            return
                        reconnect |= text.startswith('REALTIME_RECONNECT')
                if not reconnect:
                    return
                cause: BaseException = ConnectionError('REALTIME_RECONNECT')
            except (OSError, http.client.HTTPException) as exc:
                cause = exc
            finally:
                resp.close()
            if stop.is_set():  # Closed mid-read, seen as a read error or EOF.
                return
            if failures >= 3:  # Also bounds an upstream that keeps reconnecting.
                path = self._c._base_path + self._path
                raise _wire._network_error(cause, 'GET', path) from cause
            failures += 1


class AsyncRealtime:
    """The async version of :class:`Realtime`, from ``apps.realtime``.

    Use it with ``async for``, inside an ``async with`` block so that the
    feed closes when the block ends. The feed is read on its own background
    thread, so it does not occupy the thread pool that the other async calls
    use.
    """

    def __init__(self, stream: Realtime) -> None:
        self._stream = stream

    async def __aenter__(self) -> AsyncRealtime:
        """Return the feed for use in an ``async with`` block."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Close the feed when the ``async with`` block ends."""
        self.close()

    def close(self) -> None:
        """Stop the feed. It is safe to call from any thread."""
        self._stream.close()

    async def __aiter__(self) -> AsyncIterator[t.RealtimeEvent]:
        import asyncio  # ponytail: lazy, keeps `import squarecloud` ~40 ms faster

        stream, loop = self._stream, asyncio.get_running_loop()
        # ponytail: unbounded queue; a consumer slower than the feed buffers.
        queue: asyncio.Queue[Any] = asyncio.Queue()
        done = object()

        def put(item: object) -> None:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, item)
            except RuntimeError:  # The event loop is gone.
                stream.close()

        def pump() -> None:
            try:
                for event in stream:
                    put(event)
            except BaseException as exc:  # Raised again in the consumer.
                put(exc)
            put(done)

        threading.Thread(target=pump, name='squarecloud-realtime', daemon=True).start()
        try:
            while (item := await queue.get()) is not done:
                if isinstance(item, BaseException):
                    raise item
                yield item
        finally:
            stream.close()
