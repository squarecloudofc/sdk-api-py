"""Helpers for the wire format.

They cover query, JSON and time encoding, error decoding, the multipart
body, the SSE parser and the backoff wait. Callers reach ``_sleep`` through
the module as ``_wire._sleep(...)``, never as an imported name, so that the
tests can patch ``squarecloud._wire._sleep``.
"""

from __future__ import annotations

import json
import logging
import os
import random
import threading
import time
from collections.abc import Callable, Iterable, Iterator
from datetime import UTC, datetime
from typing import IO, Any
from urllib.parse import quote

from ._transport import Response
from .errors import SquareCloudAPIError

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # The upload limit of apps.create and commit.
MAX_FILE_BYTES = 10 * 1024 * 1024  # The content limit of files.write.
_NO_TIMEOUT_BYTES = 1024 * 1024  # A larger files.write is sent like an upload.
_CHUNK = 64 * 1024
_JSON = {'Content-Type': 'application/json'}
# The timeout floor of calls the server holds open before its first byte.
# Start, stop, restart and database creation take up to 95 s, and a snapshot
# create or restore answers 202 after about 90 s.
_SLOW = 120.0
_AI = 120.0  # The AI gateway answers within its 90 s deadline.
_BUSY = frozenset({'UPLOAD_BUSY', 'ANALYTICS_BUSY'})

log = logging.getLogger('squarecloud')
log.addHandler(logging.NullHandler())


def _sleep(seconds: float, stop: threading.Event | None = None) -> None:
    """Wait ``seconds``, or less when ``stop`` is set. The tests patch it."""
    if stop is None:
        time.sleep(seconds)
    else:
        stop.wait(seconds)


UploadFile = str | os.PathLike[str] | bytes | IO[bytes]
Time = str | datetime


def _q(value: str) -> str:
    return quote(str(value), safe='')


def _json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def _iso(value: Time) -> str:
    """RFC 3339 in UTC. A naive datetime is local time, as in the stdlib."""
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')
    return value


def _delay(attempt: int) -> float:
    return min(8.0, 0.5 * 2**attempt) * random.uniform(0.5, 1.0)


def _network_error(exc: BaseException, method: str, path: str) -> SquareCloudAPIError:
    code = 'TIMEOUT' if isinstance(exc, TimeoutError) else 'NETWORK_ERROR'
    return SquareCloudAPIError(0, code, str(exc) or type(exc).__name__, method, path)


def _api_error(status: int, data: Any, method: str, path: str) -> SquareCloudAPIError:
    """Build the error of a decoded error body.

    The message is the server's own. Without one, it is ``''`` when the body
    has a code and ``HTTP <status>`` when it has none.
    """
    code = message = None
    if isinstance(data, dict):
        inner = data.get('error')
        if isinstance(inner, dict):  # The OpenAI error format of ai.chat.
            data = {**inner, 'code': inner.get('code') or inner.get('type')}
        code, message = data.get('code'), data.get('message')
    return SquareCloudAPIError(
        status,
        str(code or 'UNKNOWN_ERROR'),
        str(message or ('' if code else f'HTTP {status}')),
        method,
        path,
    )


def _failed(data: Any) -> bool:
    return isinstance(data, dict) and data.get('status') == 'error'


def _too_large(what: str, method: str, path: str) -> SquareCloudAPIError:
    return SquareCloudAPIError(0, 'FILE_TOO_LARGE', what, method, path)


class _LocalError(Exception):
    """Carry an ``OSError`` of the upload file out of the transport.

    Without it, the error would be reported as a network error.
    """


def _exactly(f: IO[bytes], size: int) -> Iterator[bytes]:
    """Yield exactly ``size`` bytes of ``f``.

    A file that shrinks during the upload fails, instead of leaving the
    server waiting for the declared length.
    """
    try:
        while size > 0:
            chunk = f.read(min(_CHUNK, size))
            if not chunk:
                raise OSError(
                    'The upload file shrank while it was being sent. Make sure '
                    'nothing changes the file until the upload ends.'
                )
            size -= len(chunk)
            yield chunk
    except OSError as exc:
        raise _LocalError(exc) from exc


def _multipart(
    file: UploadFile, path: str, filename: str | None = None, default: str = 'app.zip'
) -> tuple[Callable[[], Iterable[bytes]], dict[str, str]]:
    """Stream ``file`` as the only part, named ``file``, of a multipart body.

    The body's Content-Length is computed in advance, and the returned
    factory is called once per attempt. A missing or unreadable path raises
    ``OSError`` here, before anything is sent.
    """
    content: Callable[[], Iterable[bytes]]
    name: str | None = None
    if isinstance(file, (bytes, bytearray, memoryview)):
        data = bytes(file)
        size = len(data)

        def content() -> Iterable[bytes]:
            return (data,)
    elif isinstance(file, (str, os.PathLike)):
        fspath = os.fspath(file)
        with open(fspath, 'rb') as f:  # Fails now for a missing path or a dir.
            size = os.fstat(f.fileno()).st_size
        name = os.path.basename(fspath)

        def content() -> Iterator[bytes]:
            try:
                f = open(fspath, 'rb')  # noqa: SIM115
            except OSError as exc:
                raise _LocalError(exc) from exc
            with f:
                yield from _exactly(f, size)
    else:
        fobj = file
        raw_name = getattr(fobj, 'name', None)
        name = os.path.basename(raw_name) if isinstance(raw_name, str) else None
        if fobj.seekable():
            start = fobj.tell()
            size = fobj.seek(0, os.SEEK_END) - start
            fobj.seek(start)

            def content() -> Iterator[bytes]:
                fobj.seek(start)
                yield from _exactly(fobj, size)
        else:
            # ponytail: a pipe has no size, so it is buffered once. At most
            # the limit plus one byte is read, which is enough to reject it.
            data = fobj.read(MAX_UPLOAD_BYTES + 1)
            size = len(data)

            def content() -> Iterable[bytes]:
                return (data,)

    if size > MAX_UPLOAD_BYTES:
        raise _too_large(
            'The file is larger than the 100 MB upload limit. Leave dependency '
            'folders and build output out of the zip, or upload a smaller file.',
            'POST',
            path,
        )
    boundary = os.urandom(16).hex()
    safe = (filename or name or default).translate({34: '%22', 10: None, 13: None})
    head = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{safe}"\r\nContent-Type: application/octet-stream\r\n\r\n'
    ).encode()
    tail = f'\r\n--{boundary}--\r\n'.encode()

    def body() -> Iterator[bytes]:
        yield head
        yield from content()
        yield tail

    return body, {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(head) + size + len(tail)),
    }


def _sse(resp: Response) -> Iterator[tuple[str, str, str | None]]:
    """Parse a text/event-stream body into ``(event, data, id)`` tuples.

    An unterminated frame at the end of the stream is discarded.
    """
    event, data, last_id = 'message', list[str](), None
    for raw in iter(resp.readline, b''):
        line = raw.decode('utf-8', 'replace').removesuffix('\n').removesuffix('\r')
        if not line:
            if data:
                yield event or 'message', '\n'.join(data), last_id
            event, data = 'message', []
            continue
        field, _, value = line.partition(':')
        if value[:1] == ' ':
            value = value[1:]
        if field == 'event':
            event = value
        elif field == 'data':
            data.append(value)
        elif field == 'id' and '\0' not in value:
            last_id = value
