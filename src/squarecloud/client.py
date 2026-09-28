"""Square Cloud API client: stdlib only (``http.client`` + ``json``).

Every ``app_id`` may be the composite ``'<appId>-<workspaceId>'`` to act on
an application shared with you through a workspace.
"""

from __future__ import annotations

import base64
import builtins
import contextlib
import functools
import http.client
import io
import json
import logging
import os
import random
import select
import socket
import ssl
import sys
import threading
import time
import weakref
import zlib
from collections.abc import (
    AsyncIterator,
    Callable,
    Coroutine,
    Generator,
    Iterable,
    Iterator,
)
from datetime import UTC, datetime
from types import TracebackType
from typing import (
    IO,
    Any,
    Concatenate,
    Generic,
    Literal,
    ParamSpec,
    Protocol,
    TypeVar,
    Unpack,
    cast,
)
from urllib.parse import quote, urlencode, urlsplit

from . import types as t
from .errors import SquareCloudAPIError

# The single version source: pyproject.toml reads it (tool.hatch.version).
__version__ = '5.0.0'

BASE_URL = 'https://api.squarecloud.app/v2'
USER_AGENT = f'squarecloud-sdk-py/{__version__}'
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # zip limit of POST /apps and commit
MAX_FILE_BYTES = 10 * 1024 * 1024  # content limit of PUT files
_NO_TIMEOUT_BYTES = 1024 * 1024  # a larger files.write is sent like an upload
_CHUNK = 64 * 1024
_JSON = {'Content-Type': 'application/json'}
# Calls the server holds open before its first byte: start/stop/restart and
# database create/start/stop take up to 95 s, a snapshot answers 202 at ~90 s.
_SLOW = 120.0
_AI = 120.0  # the AI gateway answers within its 90 s deadline
_BUSY = frozenset({'UPLOAD_BUSY', 'ANALYTICS_BUSY'})

log = logging.getLogger('squarecloud')
log.addHandler(logging.NullHandler())


def _sleep(seconds: float, stop: threading.Event | None = None) -> None:
    """Waits ``seconds``, or less when ``stop`` is set. Patched by the tests."""
    if stop is None:
        time.sleep(seconds)
    else:
        stop.wait(seconds)


Body = bytes | Iterable[bytes] | None
UploadFile = str | os.PathLike[str] | bytes | IO[bytes]
Time = str | datetime


# Transport ------------------------------------------------------------------


class Response(Protocol):
    """What a transport returns. ``http.client.HTTPResponse`` fits."""

    status: int

    def read(self, amt: int | None = None, /) -> bytes: ...

    def readline(self, limit: int = -1, /) -> bytes: ...

    def close(self) -> None: ...


class Transport(Protocol):
    """Pluggable transport: ``transport(method, url, headers, body, timeout,
    stream) -> Response``. ``body`` is ``bytes``, an iterable of ``bytes``
    chunks (``Content-Length`` is already in ``headers``) or ``None``.
    ``timeout`` is ``None`` for uploads and the realtime stream. ``stream``
    means the caller reads the body incrementally and may call ``close()``
    from another thread to abort it."""

    def __call__(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: Body,
        timeout: float | None,
        stream: bool,
        /,
    ) -> Response: ...


class _Buffered(io.BytesIO):
    """A response read to the end, so its pooled connection is reusable."""

    def __init__(self, status: int, data: bytes) -> None:
        super().__init__(data)
        self.status = status


class _Stream:
    """A streamed response on its own connection. ``close()`` is safe from
    any thread: it shuts the socket down, which unblocks a pending read."""

    def __init__(
        self,
        conn: http.client.HTTPConnection,
        resp: http.client.HTTPResponse,
        sock: socket.socket,
    ) -> None:
        self.status = resp.status
        self.read = resp.read
        self.readline = resp.readline
        self._conn = conn
        self._sock = sock

    def close(self) -> None:
        with contextlib.suppress(OSError):
            self._sock.shutdown(socket.SHUT_RDWR)
        if os.name == 'nt':
            # Windows wakes a blocked recv only when the handle is closed, and
            # the makefile() reference defers socket.close(): close it for real.
            # POSIX skips this: shutdown() already wakes the reader, and an
            # early close would let the fd number be reused under it.
            with contextlib.suppress(OSError):
                super(socket.socket, self._sock).close()
        self._conn.close()


def _dropped(sock: socket.socket) -> bool:
    # An idle keep-alive socket that is readable was closed by the server.
    try:
        if sys.platform != 'win32':  # select() fails on fds >= 1024
            poller = select.poll()
            poller.register(sock, select.POLLIN)
            return bool(poller.poll(0))
        return bool(select.select([sock], [], [], 0)[0])
    except (OSError, ValueError):
        return True


@functools.cache
def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()  # loads the CA store: ~10 ms, once


class HTTPTransport:
    """Default transport: one keep-alive connection per thread and host.

    ``timeout`` bounds the connect (and a stream's wait for its response
    headers) of the calls that have no timeout of their own: uploads and
    streams. ``None`` waits forever (never pass ``0``: it makes the socket
    non-blocking). Other calls respond gzip-compressed when the server
    supports it.
    """

    def __init__(self, timeout: float | None = 30.0) -> None:
        self.timeout = timeout
        self._local = threading.local()
        self._conns: weakref.WeakSet[http.client.HTTPConnection] = weakref.WeakSet()

    def _connect(self, scheme: str, host: str) -> http.client.HTTPConnection:
        conn = (
            http.client.HTTPSConnection(host, context=_ssl_context())
            if scheme == 'https'
            else http.client.HTTPConnection(host)
        )
        self._conns.add(conn)
        return conn

    def __call__(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: Body,
        timeout: float | None,
        stream: bool,
    ) -> Response:
        u = urlsplit(url)
        target = (u.path or '/') + (f'?{u.query}' if u.query else '')
        if stream:
            conn = self._connect(u.scheme, u.netloc)
        else:
            pool: dict[str, http.client.HTTPConnection]
            pool = self._local.__dict__.setdefault('pool', {})
            key = f'{u.scheme}://{u.netloc}'
            pooled = pool.get(key)
            if pooled is None:
                pooled = pool[key] = self._connect(u.scheme, u.netloc)
            elif pooled.sock is not None and _dropped(pooled.sock):
                pooled.close()  # reconnected below
            conn = pooled
            headers = {**headers, 'Accept-Encoding': 'gzip'}
        try:
            if conn.sock is None:
                conn.timeout = self.timeout if timeout is None else timeout
                conn.connect()
            sock: socket.socket = conn.sock
            if not stream:
                sock.settimeout(timeout)  # None: an upload waits for its reply
            conn.request(method, target, body=body, headers=headers)
            resp = conn.getresponse()
            if stream:
                sock.settimeout(timeout)  # headers are in: the body may idle
                return _Stream(conn, resp, sock)
            # Read it all here: a partial read must not leave unread bytes on
            # a pooled socket, or the next request would parse them.
            data = resp.read()
            if resp.getheader('Content-Encoding') == 'gzip':
                try:
                    data = zlib.decompress(data, 47)
                except zlib.error as exc:
                    raise http.client.HTTPException(f'bad gzip body: {exc}') from exc
            return _Buffered(resp.status, data)
        except BaseException:
            conn.close()
            raise

    def close(self) -> None:
        for conn in list(self._conns):
            conn.close()


# Helpers --------------------------------------------------------------------


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
    """The error of a decoded body: the server's message, else ``''`` when
    there is a code, else ``HTTP <status>``."""
    code = message = None
    if isinstance(data, dict):
        inner = data.get('error')
        if isinstance(inner, dict):  # OpenAI dialect of POST /ai/...
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
    """Carries an ``OSError`` of the upload file out of the transport, so it
    is not reported as a network error."""


def _exactly(f: IO[bytes], size: int) -> Iterator[bytes]:
    """``size`` bytes of ``f``: a file that shrank mid-upload must fail
    rather than leave the server waiting for the declared length."""
    try:
        while size > 0:
            chunk = f.read(min(_CHUNK, size))
            if not chunk:
                raise OSError('the upload file shrank while it was being sent')
            size -= len(chunk)
            yield chunk
    except OSError as exc:
        raise _LocalError(exc) from exc


def _multipart(
    file: UploadFile, path: str, filename: str | None = None, default: str = 'app.zip'
) -> tuple[Callable[[], Iterable[bytes]], dict[str, str]]:
    """Streams ``file`` as the single ``file`` part of a multipart body with
    a precomputed Content-Length. The factory is called once per attempt.
    A missing or unreadable path raises ``OSError`` here, before sending."""
    content: Callable[[], Iterable[bytes]]
    name: str | None = None
    if isinstance(file, (bytes, bytearray, memoryview)):
        data = bytes(file)
        size = len(data)

        def content() -> Iterable[bytes]:
            return (data,)
    elif isinstance(file, (str, os.PathLike)):
        fspath = os.fspath(file)
        with open(fspath, 'rb') as f:  # fails now for a missing path or a dir
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
            # ponytail: a pipe has no size, so it is buffered once (at most
            # the limit plus one byte, enough to reject it).
            data = fobj.read(MAX_UPLOAD_BYTES + 1)
            size = len(data)

            def content() -> Iterable[bytes]:
                return (data,)

    if size > MAX_UPLOAD_BYTES:
        raise _too_large('Uploads are limited to 100 MB', 'POST', path)
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
    """Minimal text/event-stream parser: yields ``(event, data, id)``. An
    unterminated frame at the end of the stream is discarded."""
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


# Client ---------------------------------------------------------------------


class SquareCloud:
    """Synchronous client. Thread-safe: each thread reuses its own
    keep-alive connection.

    >>> client = SquareCloud('API_KEY')
    >>> client.apps.status('0123456789abcdef0123456789abcdef')
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
        transport: Transport | None = None,
        user_agent: str = USER_AGENT,
    ) -> None:
        """``timeout`` (seconds, per socket operation) ``<= 0`` disables
        every timeout, the floors of held and AI calls included."""
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError('api_key must be a non-empty string')
        self._base_url = base_url.rstrip('/')
        self._base_path = urlsplit(self._base_url).path  # '/v2': error paths
        self._timeout = timeout
        self._max_retries = max_retries
        self._transport: Transport = transport or HTTPTransport(
            timeout if timeout > 0 else None
        )
        self._user_agent = user_agent
        self._headers = {
            'Authorization': api_key,
            'User-Agent': user_agent,
            'Accept': 'application/json',
        }
        self.account = Account(self)
        self.service = Service(self)
        self.ai = AI(self)
        self.apps = Apps(self)
        self.databases = Databases(self)
        self.workspaces = Workspaces(self)

    def __enter__(self) -> SquareCloud:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """Closes the pooled connections (only of the default transport)."""
        close = getattr(self._transport, 'close', None)
        if close is not None:
            close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        json_body: Any = None,
        body: bytes | Callable[[], Iterable[bytes]] | None = None,
        headers: dict[str, str] | None = None,
        no_timeout: bool = False,
        min_timeout: float = 0.0,
        raw: bool = False,
        stream: bool = False,
        url: str | None = None,
        stop: threading.Event | None = None,
    ) -> Any:
        """Sends one call under the retry policy: network errors (not
        timeouts) retry only on GET, 503 UPLOAD_BUSY/ANALYTICS_BUSY retry on
        any method, 503 DATABASE_UNAVAILABLE only on GET (it can fire after a
        mutation was applied), 429 never.
        ``min_timeout`` raises the timeout of a call the server holds open.
        A 2xx ``{status: 'error'}`` body raises unless ``raw`` (routes
        without the envelope) or 202 (pending). Returns the decoded JSON
        body, or the open 2xx response when ``stream``. A set ``stop`` ends
        a retry wait at once and raises its error."""
        max_retries = self._max_retries
        if url is None:
            if any(s in ('', '.', '..') for s in path.split('/')[1:]):
                raise SquareCloudAPIError(
                    0,
                    'INVALID_ID',
                    'Empty, "." and ".." are not valid ids',
                    method,
                    self._base_path + path,
                )
            # Absent, '' and False are dropped; True is sent as 'true'.
            params = {
                k: 'true' if v is True else v
                for k, v in (query or {}).items()
                if v is not None and v is not False and v != ''
            }
            url = self._base_url + path + (f'?{urlencode(params)}' if params else '')
            hdrs = dict(self._headers)
        else:  # a foreign host (snapshot download): never send the key
            hdrs = {'User-Agent': self._user_agent}
        if json_body is not None:
            body = _json(json_body)
            hdrs.update(_JSON)
        if headers:
            hdrs.update(headers)
        timeout = (
            None
            if no_timeout or self._timeout <= 0
            else max(self._timeout, min_timeout)
        )
        path = urlsplit(url).path  # errors report the full path, e.g. /v2/...
        attempt = 0
        while True:
            payload = body() if callable(body) else body
            try:
                resp = self._transport(method, url, hdrs, payload, timeout, stream)
                if stream and resp.status < 300:
                    return resp
                try:
                    body_raw = resp.read()
                finally:
                    resp.close()
            except _LocalError as exc:
                raise exc.args[0] from None
            except (OSError, http.client.HTTPException) as exc:
                if (
                    method != 'GET'
                    or attempt >= max_retries
                    or isinstance(exc, TimeoutError)  # never waits twice
                ):
                    raise _network_error(exc, method, path) from exc
                log.debug('%s %s: %r, retrying', method, path, exc)
                _sleep(_delay(attempt), stop)
                if stop is not None and stop.is_set():
                    raise _network_error(exc, method, path) from exc
                attempt += 1
                continue
            finally:
                # A failed send leaves the upload generator (and the file it
                # holds open) referenced by the error's traceback: close it.
                if isinstance(payload, Generator):
                    payload.close()
            status = resp.status
            log.debug('%s %s -> %d', method, path, status)
            try:
                data = json.loads(body_raw) if body_raw else {}
            except ValueError as exc:  # HTML from a proxy, S3 XML...
                ok = status < 300
                raise SquareCloudAPIError(
                    status,
                    'UNKNOWN_ERROR',
                    f'Invalid JSON in HTTP {status} response'
                    if ok
                    else f'HTTP {status}',
                    method,
                    path,
                ) from (exc if ok else None)
            if status < 300 and (
                # safety net: a 2xx {status: 'error'} is still a failure
                raw or status == 202 or not _failed(data)
            ):
                return data
            error = _api_error(status, data, method, path)
            if (
                status == 503
                and attempt < max_retries
                and (
                    error.code in _BUSY
                    or (method == 'GET' and error.code == 'DATABASE_UNAVAILABLE')
                )
            ):
                _sleep(_delay(attempt), stop)
                if stop is None or not stop.is_set():
                    attempt += 1
                    continue
            raise error

    def _r(self, method: str, path: str, **kwargs: Any) -> Any:
        """``_request`` unwrapped from the ``{status, response}`` envelope."""
        data = self._request(method, path, **kwargs)
        return data.get('response') if isinstance(data, dict) else data

    def download_snapshot(self, url: str, dest: str | os.PathLike[str]) -> str:
        """Streams a snapshot ``url`` (from ``snapshots.create``) to ``dest``
        (a file path, or a directory to keep the remote file name; a path
        ending in a separator is created as a directory). Returns the written
        path. The file appears only once complete, so a failed download
        never clobbers an earlier one. The API key is never sent to the
        snapshot host. Local file errors raise ``OSError``."""
        target = os.fspath(dest)
        remote = urlsplit(url).path
        if target.endswith(('/', os.sep)):
            os.makedirs(target, exist_ok=True)
        if os.path.isdir(target):
            name = os.path.basename(remote) or 'snapshot.zip'
            target = os.path.join(target, name)
        resp: Response = self._request('GET', remote, url=url, stream=True)
        part = target + '.part'
        try:
            with open(part, 'wb') as f:
                while True:
                    try:
                        chunk = resp.read(_CHUNK)
                    except (OSError, http.client.HTTPException) as exc:
                        raise _network_error(exc, 'GET', remote) from exc
                    if not chunk:
                        break
                    f.write(chunk)
            os.replace(part, target)
        except BaseException:
            with contextlib.suppress(OSError):
                os.remove(part)
            raise
        finally:
            resp.close()
        return target


class _Group:
    def __init__(self, client: SquareCloud) -> None:
        self._c = client


class Account(_Group):
    def me(self) -> t.Account:
        """``GET /users/me``: the user plus their apps and databases."""
        return self._c._r('GET', '/users/me')

    def snapshots(self, *, scope: t.SnapshotScope | None = None) -> list[t.Snapshot]:
        """``GET /users/snapshots``: every snapshot of the account. Each item
        carries ``version_id`` and a signed download ``url``."""
        return self._c._r('GET', '/users/snapshots', query={'scope': scope})


class Service(_Group):
    def status(self) -> t.ServiceStatus:
        """``GET /service/status`` (public; not enveloped)."""
        return self._c._request('GET', '/service/status', raw=True)


class AI(_Group):
    def chat(self, request: t.ChatRequest | dict[str, Any]) -> t.ChatCompletion:
        """``POST /ai/chat/completions`` (OpenAI-compatible, no streaming).
        ``request`` is sent as the body, so any OpenAI parameter passes
        through. The gateway has one 90 s deadline for the whole request
        and answers 503 ``server_overloaded`` past it: safe to retry, but the
        SDK does not (the timeout floor is 120 s). Errors of both dialects
        become :class:`SquareCloudAPIError`."""
        return self._c._request(
            'POST', '/ai/chat/completions', json_body=request, raw=True, min_timeout=_AI
        )


class Apps(_Group):
    """Applications. ``app_id`` may be ``'<appId>-<workspaceId>'``."""

    def __init__(self, client: SquareCloud) -> None:
        super().__init__(client)
        self.deploys = Deploys(client)
        self.envs = Envs(client)
        self.files = Files(client)
        self.snapshots = Snapshots(client, '/apps')
        self.network = Network(client)

    def create(self, file: UploadFile) -> t.AppCreated:
        """``POST /apps``: uploads a zip (path, bytes or binary file),
        streamed from disk."""
        body, headers = _multipart(file, self._c._base_path + '/apps')
        return self._c._r('POST', '/apps', body=body, headers=headers, no_timeout=True)

    def get(self, app_id: str) -> t.App:
        return self._c._r('GET', f'/apps/{_q(app_id)}')

    def delete(self, app_id: str) -> None:
        self._c._request('DELETE', f'/apps/{_q(app_id)}')

    def status_all(self, *, workspace_id: str | None = None) -> list[t.StatusListItem]:
        """``GET /apps/status``, including stopped apps."""
        return self._c._r('GET', '/apps/status', query={'workspaceId': workspace_id})

    def status(self, app_id: str, *, raw: bool = False) -> t.RuntimeStats:
        """Formatted strings (``ram`` e.g. ``'120.4MB'``); ``raw=True``
        returns numbers instead."""
        return self._c._r(
            'GET',
            f'/apps/{_q(app_id)}/status',
            query={'rawData': 'true' if raw else None},
        )

    def start(self, app_id: str) -> None:
        """Starts the app. A refusal is 409 with a code and no message:
        ``CONTAINER_ALREADY_STARTED``, ``CONTAINER_ALREADY_STOPPED``,
        ``CONTAINER_TEMPORARILY_SUSPENDED``, ``CONTAINER_NOT_FOUND``,
        ``CONTAINER_INSUFFICIENT_DISK_SPACE``, ``CONTAINER_NETWORK_CONFLICT``
        or ``ACTION_FAILED``. The same holds for ``stop`` and ``restart``."""
        self._c._request('POST', f'/apps/{_q(app_id)}/start', min_timeout=_SLOW)

    def stop(self, app_id: str) -> None:
        """Stops the app; 409 refusals as in :meth:`start`."""
        self._c._request('POST', f'/apps/{_q(app_id)}/stop', min_timeout=_SLOW)

    def restart(self, app_id: str) -> None:
        """Restarts the app; 409 refusals as in :meth:`start`."""
        self._c._request('POST', f'/apps/{_q(app_id)}/restart', min_timeout=_SLOW)

    def logs(self, app_id: str) -> str:
        """The latest logs as one string."""
        return str(
            (self._c._r('GET', f'/apps/{_q(app_id)}/logs') or {}).get('logs') or ''
        )

    def metrics(self, app_id: str) -> list[t.MetricPoint]:
        """Up to 24 h of 5-minute points, newest first."""
        return self._c._r('GET', f'/apps/{_q(app_id)}/metrics')

    def realtime(self, app_id: str) -> Realtime:
        """``GET /apps/{appId}/realtime`` as an iterator of
        :class:`~squarecloud.types.RealtimeEvent`. Call ``close()`` (from
        any thread) or leave the ``with`` block to stop."""
        return Realtime(self._c, f'/apps/{_q(app_id)}/realtime')

    def domains(self) -> list[t.AppDomain]:
        return self._c._r('GET', '/apps/domains')

    def load_balancers(self) -> t.LoadBalancers:
        return self._c._r('GET', '/apps/load-balancers')

    def commit(
        self,
        app_id: str,
        file: UploadFile,
        *,
        path: str | None = None,
        filename: str | None = None,
    ) -> None:
        """``POST /apps/{appId}/commit``: a ``.zip`` is unpacked into
        ``path`` (the app root by default); any other file is placed at
        ``path/<filename>``. ``filename`` defaults to the file's own name,
        or ``'commit.zip'`` for ``bytes`` and unnamed streams."""
        endpoint = f'/apps/{_q(app_id)}/commit'
        body, headers = _multipart(
            file, self._c._base_path + endpoint, filename, 'commit.zip'
        )
        self._c._request(
            'POST',
            endpoint,
            query={'path': path},
            body=body,
            headers=headers,
            no_timeout=True,
        )


class Deploys(_Group):
    def set_webhook(self, app_id: str, access_token: str) -> str:
        """Configures the Git webhook; returns its URL."""
        r = self._c._r(
            'POST',
            f'/apps/{_q(app_id)}/deploy/webhook',
            json_body={'access_token': access_token},
        )
        return str((r or {}).get('webhook') or '')

    def link_github_app(
        self, app_id: str, repository: str, branch: str
    ) -> t.LinkedRepository:
        """Links ``repository`` (``'owner/name'``) at ``branch`` through the
        Square Cloud GitHub App (scope ``apps:deploy``; 3 calls per 60 s).
        A linked app must be unlinked before it can be linked again (400
        ``GIT_ALREADY_CONFIGURED``). 403 ``GITHUB_NOT_CONNECTED``: your
        account has no GitHub App installation; 403
        ``REPOSITORY_NOT_AVAILABLE``: no
        GitHub App installation of your account covers the repository; 403
        ``REPOSITORY_PERMISSION_REQUIRED``: no write access to it; 502
        ``FAILED_TO_FETCH``: GitHub did not confirm the branch (safe to
        retry); 409 ``REPOSITORY_BRANCH_ALREADY_CONFIGURED``: another app, of
        any account, links the same repository and branch (its id appears
        only in ``message``, and only when that app is yours)."""
        r = self._c._r(
            'POST',
            f'/apps/{_q(app_id)}/deploy/github-app',
            json_body={'repositoryName': repository, 'repositoryBranch': branch},
        )
        # ponytail: a 2xx without it (a relayed auth-service body) gives {},
        # like GO's zero value, never a KeyError.
        return cast(t.LinkedRepository, (r or {}).get('repository') or {})

    def unlink_github_app(self, app_id: str) -> None:
        """Removes the GitHub App link (400 ``GIT_NOT_CONFIGURED`` if none)."""
        self._c._request('DELETE', f'/apps/{_q(app_id)}/deploy/github-app')

    def list(self, app_id: str) -> builtins.list[builtins.list[t.DeployEvent]]:
        """The latest deploys, each one a list of state events. A failed
        deploy ends with ``state='error'`` and carries ``code`` and
        ``message``."""
        return self._c._r('GET', f'/apps/{_q(app_id)}/deployments')

    def current(self, app_id: str) -> t.DeployCurrent:
        path = f'/apps/{_q(app_id)}/deployments/current'
        return self._c._r('GET', path) or t.DeployCurrent()


class Envs(_Group):
    def get(self, app_id: str) -> t.EnvVars:
        return self._c._r('GET', f'/apps/{_q(app_id)}/envs')

    def set(self, app_id: str, envs: t.EnvVars) -> t.EnvVars:
        """Adds or updates the given variables; returns all of them."""
        return self._c._r('POST', f'/apps/{_q(app_id)}/envs', json_body={'envs': envs})

    def replace(self, app_id: str, envs: t.EnvVars) -> t.EnvVars:
        """Replaces every variable (``{}`` clears them)."""
        return self._c._r('PUT', f'/apps/{_q(app_id)}/envs', json_body={'envs': envs})

    def delete(self, app_id: str, keys: str | Iterable[str]) -> t.EnvVars:
        """Removes one variable or several; returns the remaining ones."""
        names = [keys] if isinstance(keys, str) else list(keys)
        return self._c._r(
            'DELETE', f'/apps/{_q(app_id)}/envs', json_body={'envs': names}
        )


class Files(_Group):
    def list(self, app_id: str, path: str | None = None) -> builtins.list[t.FileEntry]:
        """Lists a directory (the app root by default). A missing directory
        is 404 ``FILE_NOT_FOUND``, a blocked one 403 ``BLOCKED_PATH``. Paths
        are at most 256 characters."""
        return self._c._r('GET', f'/apps/{_q(app_id)}/files', query={'path': path})

    def read(self, app_id: str, path: str) -> bytes:
        """The file's bytes (at most 10 MB, else 413 ``FILE_TOO_LARGE``),
        fetched base64-encoded."""
        r = self._c._r(
            'GET',
            f'/apps/{_q(app_id)}/files/content',
            query={'path': path, 'encoding': 'base64'},
        )
        return base64.b64decode((r or {}).get('data') or '')

    def write(self, app_id: str, path: str, content: str | bytes) -> None:
        """Creates or overwrites a file (at most 10 MB). A ``str`` travels as
        text, ``bytes`` base64-encoded. Empty content writes an empty file.
        Content over 1 MiB is sent without a timeout, like an upload."""
        endpoint = f'/apps/{_q(app_id)}/files'
        # A char is at least one byte: big text is rejected before encoding.
        too_large = len(content) > MAX_FILE_BYTES
        if not too_large:
            data = content.encode() if isinstance(content, str) else bytes(content)
            too_large = len(data) > MAX_FILE_BYTES
        if too_large:
            raise _too_large(
                'File content is limited to 10 MB', 'PUT', self._c._base_path + endpoint
            )
        body = (
            {'path': path, 'content': content}
            if isinstance(content, str)
            else {
                'path': path,
                'content': base64.b64encode(data).decode(),
                'encoding': 'base64',
            }
        )
        self._c._request(
            'PUT',
            endpoint,
            json_body=body,
            no_timeout=len(data) > _NO_TIMEOUT_BYTES,  # sent like an upload
        )

    def move(self, app_id: str, path: str, to: str) -> None:
        """Moves or renames ``path`` to ``to``."""
        self._c._request(
            'PATCH',
            f'/apps/{_q(app_id)}/files',
            json_body={'path': path, 'to': to},
        )

    def delete(self, app_id: str, path: str) -> None:
        self._c._request(
            'DELETE', f'/apps/{_q(app_id)}/files', json_body={'path': path}
        )


class Snapshots(_Group):
    """Snapshots of an app (``apps.snapshots``) or a database
    (``databases.snapshots``)."""

    def __init__(self, client: SquareCloud, prefix: str) -> None:
        super().__init__(client)
        self._prefix = prefix

    def list(self, resource_id: str) -> builtins.list[t.Snapshot]:
        """Each item carries ``version_id`` (for ``restore``) and a signed
        download ``url``, as the API sends them."""
        return self._c._r('GET', f'{self._prefix}/{_q(resource_id)}/snapshots')

    def create(self, resource_id: str) -> t.SnapshotCreated:
        """Returns ``{'pending': False, 'url', 'key'}``, or
        ``{'pending': True}`` (HTTP 202 ``SNAPSHOT_PROCESSING``) when the
        snapshot is still being generated: it then appears in ``list`` on its
        own, usually within 2 minutes. Poll ``list``, never call ``create``
        again: it is limited to one per 180 s and counts against the plan's
        daily snapshot quota."""
        r = self._c._r(
            'POST', f'{self._prefix}/{_q(resource_id)}/snapshots', min_timeout=_SLOW
        )
        return cast(
            t.SnapshotCreated, {'pending': False, **r} if r else {'pending': True}
        )

    def restore(self, resource_id: str, name: str, version_id: str) -> None:
        """Restores the snapshot ``name`` at ``version_id`` (both from
        ``list``)."""
        self._c._request(
            'POST',
            f'{self._prefix}/{_q(resource_id)}/snapshots/restore',
            json_body={'snapshotId': name, 'versionId': version_id},
            min_timeout=_SLOW,
        )


class Network(_Group):
    def analytics(
        self,
        app_id: str,
        start: Time,
        end: Time,
        **filters: Unpack[t.AnalyticsFilters],
    ) -> t.NetworkAnalytics | None:
        """``None`` when the window has no data. ``filters`` are keyword-only
        (``country='BR'``, ``status='404'``, ``provider='GOOGLE (15169)'``:
        the ``type`` of a ``providers`` item); an invalid one is 400
        ``INVALID_FILTER``."""
        query = {'start': _iso(start), 'end': _iso(end), **filters}
        endpoint = f'/apps/{_q(app_id)}/network/analytics'
        return self._c._r('GET', endpoint, query=query) or None

    def errors(
        self, app_id: str, start: Time, end: Time, *, include_4xx: bool = False
    ) -> t.NetworkErrors | None:
        """``None`` when the window has no data."""
        query = {
            'start': _iso(start),
            'end': _iso(end),
            'include_4xx': 'true' if include_4xx else None,
        }
        endpoint = f'/apps/{_q(app_id)}/network/errors'
        return self._c._r('GET', endpoint, query=query) or None

    def logs(self, app_id: str, start: Time, end: Time) -> list[t.NetworkLog]:
        return self._c._r(
            'GET',
            f'/apps/{_q(app_id)}/network/logs',
            query={'start': _iso(start), 'end': _iso(end)},
        )

    def performance(
        self, app_id: str, start: Time, end: Time
    ) -> t.NetworkPerformance | None:
        """``None`` when the window has no data."""
        return (
            self._c._r(
                'GET',
                f'/apps/{_q(app_id)}/network/performance',
                query={'start': _iso(start), 'end': _iso(end)},
            )
            or None
        )

    def dns(self, app_id: str) -> list[t.DNSRecord]:
        return self._c._r('GET', f'/apps/{_q(app_id)}/network/dns')

    def set_domain(self, app_id: str, domain: str) -> None:
        """Sets the custom domain of a website."""
        self._c._request(
            'POST',
            f'/apps/{_q(app_id)}/network/custom',
            json_body={'custom': domain},
        )

    def purge_cache(self, app_id: str) -> None:
        self._c._request('POST', f'/apps/{_q(app_id)}/network/purge_cache')


class Databases(_Group):
    def __init__(self, client: SquareCloud) -> None:
        super().__init__(client)
        self.snapshots = Snapshots(client, '/databases')

    def create(
        self, name: str, *, type: t.DatabaseType, version: str, memory: int
    ) -> t.DatabaseCreated:
        """``version`` may be a major prefix such as ``'8'``. ``memory`` is
        an ``int`` in MB (a float or a string gets 400 ``INVALID_MEMORY``).
        The returned ``password`` and ``certificate`` are shown only
        once."""
        return self._c._r(
            'POST',
            '/databases',
            json_body={
                'name': name,
                'type': type,
                'version': version,
                'memory': memory,
            },
            min_timeout=_SLOW,
        )

    def get(self, database_id: str) -> t.Database:
        return self._c._r('GET', f'/databases/{_q(database_id)}')

    def update(
        self,
        database_id: str,
        *,
        name: str | None = None,
        ram: int | None = None,
    ) -> None:
        body = {'name': name, 'ram': ram}
        self._c._request(
            'PATCH',
            f'/databases/{_q(database_id)}',
            json_body={k: v for k, v in body.items() if v is not None},
        )

    def delete(self, database_id: str) -> None:
        self._c._request('DELETE', f'/databases/{_q(database_id)}')

    def start(self, database_id: str) -> None:
        """Starts the database. A refusal is 409 with a code:
        ``CONTAINER_ALREADY_STARTED``, ``CONTAINER_ALREADY_STOPPED``,
        ``CONTAINER_NOT_FOUND``, ``CONTAINER_INSUFFICIENT_DISK_SPACE``,
        ``CONTAINER_NETWORK_CONFLICT`` or ``ACTION_FAILED``. The same holds
        for ``stop``."""
        self._c._request(
            'POST', f'/databases/{_q(database_id)}/start', min_timeout=_SLOW
        )

    def stop(self, database_id: str) -> None:
        """Stops the database; 409 refusals as in :meth:`start`."""
        self._c._request(
            'POST', f'/databases/{_q(database_id)}/stop', min_timeout=_SLOW
        )

    def status(self, database_id: str, *, raw: bool = False) -> t.RuntimeStats:
        return self._c._r(
            'GET',
            f'/databases/{_q(database_id)}/status',
            query={'rawData': 'true' if raw else None},
        )

    def metrics(self, database_id: str) -> list[t.MetricPoint]:
        """Up to 24 h of 5-minute points, newest first."""
        return self._c._r('GET', f'/databases/{_q(database_id)}/metrics')

    def status_all(self) -> list[t.StatusListItem]:
        return self._c._r('GET', '/databases/status')

    def certificate(self, database_id: str) -> str:
        """The certificate bundle as base64 (``base64.b64decode`` gives
        the PEM)."""
        r = self._c._r('GET', f'/databases/{_q(database_id)}/credentials/certificate')
        return str((r or {}).get('certificate') or '')

    def reset_credentials(
        self, database_id: str, reset: Literal['password', 'certificate']
    ) -> str:
        """Returns the new password (``''`` for a certificate reset)."""
        r = self._c._r(
            'POST',
            f'/databases/{_q(database_id)}/credentials/reset',
            json_body={'reset': reset},
        )
        return str((r or {}).get('password') or '')


class Workspaces(_Group):
    def __init__(self, client: SquareCloud) -> None:
        super().__init__(client)
        self.members = Members(client)
        self.apps = WorkspaceApps(client)

    def create(self, name: str) -> t.WorkspaceCreated:
        return self._c._r('POST', '/workspaces', json_body={'name': name})

    def list(self) -> builtins.list[t.Workspace]:
        return self._c._r('GET', '/workspaces')

    def get(self, workspace_id: str) -> t.Workspace:
        return self._c._r('GET', f'/workspaces/{_q(workspace_id)}')

    def delete(self, workspace_id: str) -> None:
        self._c._request(
            'DELETE', '/workspaces', json_body={'workspaceId': workspace_id}
        )

    def leave(self, workspace_id: str) -> None:
        self._c._request(
            'DELETE', '/workspaces/leave', json_body={'workspaceId': workspace_id}
        )


class Members(_Group):
    def add(self, workspace_id: str, code: str, group: t.WorkspaceGroup) -> None:
        """Adds the user behind invite ``code`` with ``group``."""
        self._c._request(
            'POST',
            '/workspaces/members',
            json_body={'workspaceId': workspace_id, 'code': code, 'group': group},
        )

    def update(
        self, workspace_id: str, member_id: str, group: t.WorkspaceGroup
    ) -> None:
        self._c._request(
            'PATCH',
            '/workspaces/members',
            json_body={
                'workspaceId': workspace_id,
                'memberId': member_id,
                'group': group,
            },
        )

    def remove(self, workspace_id: str, member_id: str) -> None:
        self._c._request(
            'DELETE',
            '/workspaces/members',
            json_body={'workspaceId': workspace_id, 'memberId': member_id},
        )

    def invite_code(self) -> str:
        """Your own invite code, to share with a workspace owner."""
        return str(
            (self._c._r('GET', '/workspaces/members/code') or {}).get('code') or ''
        )


class WorkspaceApps(_Group):
    def add(self, workspace_id: str, app_id: str) -> None:
        self._c._request(
            'POST',
            '/workspaces/applications',
            json_body={'workspaceId': workspace_id, 'appId': app_id},
        )

    def remove(self, workspace_id: str, app_id: str) -> None:
        self._c._request(
            'DELETE',
            '/workspaces/applications',
            json_body={'workspaceId': workspace_id, 'appId': app_id},
        )


# Realtime -------------------------------------------------------------------


# The API admits one realtime open per (user, app) every 5 s; 0.5 s for skew.
_REOPEN_GAP = 5.5


class Realtime:
    """Iterator over the realtime SSE feed of an app.

    ``data`` is always the raw frame text. Log events add ``stream`` (from
    the ``\\u0001``/``\\u0002`` prefix) and ``line``; status events add
    ``status``, the lean frames merged onto the last full one. A dropped
    connection, or a ``REALTIME_RECONNECT`` from the server, is reopened up
    to 3 times in a row (a log or status event resets the count), at most
    once per 5.5 s (the API's pace). Every open is a GET under
    ``max_retries``; an open that still fails raises. The iteration ends on
    a clean end of stream or on ``REALTIME_DISCONNECTED``. The stream has no
    read timeout: a half-open connection (a laptop resuming from sleep)
    blocks until ``close()``.
    """

    def __init__(self, client: SquareCloud, path: str) -> None:
        self._c = client
        self._path = path
        self._resp: Response | None = None
        self._stop = threading.Event()

    def __enter__(self) -> Realtime:
        return self

    def __exit__(
        self,
        _type: type[BaseException] | None,
        _value: BaseException | None,
        _tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Stops the stream, even mid-wait; safe to call from another thread."""
        self._stop.set()
        if self._resp is not None:
            self._resp.close()

    def __iter__(self) -> Iterator[t.RealtimeEvent]:
        failures = 0  # consecutive: a log or status event resets it
        state: dict[str, Any] = {}
        opened: float | None = None
        stop = self._stop
        while not stop.is_set():
            if opened is not None:  # a reopen: back off, at the API's pace
                since = time.monotonic() - opened
                _sleep(max(_delay(failures - 1), _REOPEN_GAP - since), stop)
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
                if stop.is_set():  # closed during a retry wait
                    return
                raise
            self._resp = resp
            if stop.is_set():  # closed while connecting
                resp.close()
                return
            reconnect = False
            try:
                for event, text, event_id in _sse(resp):
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
                        # a malformed frame keeps the last status
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
            if stop.is_set():  # closed mid-read: a read error or an early EOF
                return
            if failures >= 3:  # also bounds an upstream that keeps reconnecting
                path = self._c._base_path + self._path
                raise _network_error(cause, 'GET', path) from cause
            failures += 1


class AsyncRealtime:
    """Async iterator over :class:`Realtime`: a reader thread feeds an
    ``asyncio.Queue``, so no executor thread is held for the stream."""

    def __init__(self, stream: Realtime) -> None:
        self._stream = stream

    async def __aenter__(self) -> AsyncRealtime:
        return self

    async def __aexit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
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
            except RuntimeError:  # the loop is gone
                stream.close()

        def pump() -> None:
            try:
                for event in stream:
                    put(event)
            except BaseException as exc:  # handed to the consumer
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


# Async facade ---------------------------------------------------------------

P = ParamSpec('P')
R = TypeVar('R')


class _aio(Generic[P, R]):
    """Exposes a sync method as a coroutine run in ``asyncio.to_thread``."""

    def __init__(self, fn: Callable[Concatenate[Any, P], R]) -> None:
        self._fn = fn
        self.__doc__ = fn.__doc__

    def __get__(
        self, obj: Any, owner: type | None = None
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        if obj is None:  # class access (help(), inspect)
            return self  # type: ignore[return-value]
        fn, sync = self._fn, obj._sync

        async def call(*args: P.args, **kwargs: P.kwargs) -> R:
            import asyncio

            return await asyncio.to_thread(fn, sync, *args, **kwargs)

        return call


class _AsyncGroup:
    def __init__(self, sync: Any) -> None:
        self._sync = sync


class AsyncAccount(_AsyncGroup):
    me = _aio(Account.me)
    snapshots = _aio(Account.snapshots)


class AsyncService(_AsyncGroup):
    status = _aio(Service.status)


class AsyncAI(_AsyncGroup):
    chat = _aio(AI.chat)


class AsyncDeploys(_AsyncGroup):
    set_webhook = _aio(Deploys.set_webhook)
    link_github_app = _aio(Deploys.link_github_app)
    unlink_github_app = _aio(Deploys.unlink_github_app)
    list = _aio(Deploys.list)
    current = _aio(Deploys.current)


class AsyncEnvs(_AsyncGroup):
    get = _aio(Envs.get)
    set = _aio(Envs.set)
    replace = _aio(Envs.replace)
    delete = _aio(Envs.delete)


class AsyncFiles(_AsyncGroup):
    list = _aio(Files.list)
    read = _aio(Files.read)
    write = _aio(Files.write)
    move = _aio(Files.move)
    delete = _aio(Files.delete)


class AsyncSnapshots(_AsyncGroup):
    list = _aio(Snapshots.list)
    create = _aio(Snapshots.create)
    restore = _aio(Snapshots.restore)


class AsyncNetwork(_AsyncGroup):
    analytics = _aio(Network.analytics)
    errors = _aio(Network.errors)
    logs = _aio(Network.logs)
    performance = _aio(Network.performance)
    dns = _aio(Network.dns)
    set_domain = _aio(Network.set_domain)
    purge_cache = _aio(Network.purge_cache)


class AsyncApps(_AsyncGroup):
    def __init__(self, sync: Apps) -> None:
        super().__init__(sync)
        self.deploys = AsyncDeploys(sync.deploys)
        self.envs = AsyncEnvs(sync.envs)
        self.files = AsyncFiles(sync.files)
        self.snapshots = AsyncSnapshots(sync.snapshots)
        self.network = AsyncNetwork(sync.network)

    create = _aio(Apps.create)
    get = _aio(Apps.get)
    delete = _aio(Apps.delete)
    status_all = _aio(Apps.status_all)
    status = _aio(Apps.status)
    start = _aio(Apps.start)
    stop = _aio(Apps.stop)
    restart = _aio(Apps.restart)
    logs = _aio(Apps.logs)
    metrics = _aio(Apps.metrics)
    domains = _aio(Apps.domains)
    load_balancers = _aio(Apps.load_balancers)
    commit = _aio(Apps.commit)

    def realtime(self, app_id: str) -> AsyncRealtime:
        """Async version of :meth:`Apps.realtime`: ``async for`` over it,
        ideally inside ``async with`` so leaving the block closes it."""
        return AsyncRealtime(self._sync.realtime(app_id))


class AsyncDatabases(_AsyncGroup):
    def __init__(self, sync: Databases) -> None:
        super().__init__(sync)
        self.snapshots = AsyncSnapshots(sync.snapshots)

    create = _aio(Databases.create)
    get = _aio(Databases.get)
    update = _aio(Databases.update)
    delete = _aio(Databases.delete)
    start = _aio(Databases.start)
    stop = _aio(Databases.stop)
    status = _aio(Databases.status)
    metrics = _aio(Databases.metrics)
    status_all = _aio(Databases.status_all)
    certificate = _aio(Databases.certificate)
    reset_credentials = _aio(Databases.reset_credentials)


class AsyncMembers(_AsyncGroup):
    add = _aio(Members.add)
    update = _aio(Members.update)
    remove = _aio(Members.remove)
    invite_code = _aio(Members.invite_code)


class AsyncWorkspaceApps(_AsyncGroup):
    add = _aio(WorkspaceApps.add)
    remove = _aio(WorkspaceApps.remove)


class AsyncWorkspaces(_AsyncGroup):
    def __init__(self, sync: Workspaces) -> None:
        super().__init__(sync)
        self.members = AsyncMembers(sync.members)
        self.apps = AsyncWorkspaceApps(sync.apps)

    create = _aio(Workspaces.create)
    list = _aio(Workspaces.list)
    get = _aio(Workspaces.get)
    delete = _aio(Workspaces.delete)
    leave = _aio(Workspaces.leave)


class AsyncSquareCloud:
    """``await`` facade over :class:`SquareCloud`: same groups and methods,
    each call runs in ``asyncio.to_thread``."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
        transport: Transport | None = None,
        user_agent: str = USER_AGENT,
    ) -> None:
        self._sync = SquareCloud(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            transport=transport,
            user_agent=user_agent,
        )
        self.account = AsyncAccount(self._sync.account)
        self.service = AsyncService(self._sync.service)
        self.ai = AsyncAI(self._sync.ai)
        self.apps = AsyncApps(self._sync.apps)
        self.databases = AsyncDatabases(self._sync.databases)
        self.workspaces = AsyncWorkspaces(self._sync.workspaces)

    async def __aenter__(self) -> AsyncSquareCloud:
        return self

    async def __aexit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self._sync.close()

    async def download_snapshot(self, url: str, dest: str | os.PathLike[str]) -> str:
        import asyncio

        return await asyncio.to_thread(self._sync.download_snapshot, url, dest)
