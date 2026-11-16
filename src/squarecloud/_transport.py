"""The HTTP transport interface and the default transport."""

from __future__ import annotations

import contextlib
import functools
import http.client
import io
import os
import select
import socket
import ssl
import sys
import threading
import weakref
import zlib
from collections.abc import Iterable
from typing import Protocol
from urllib.parse import urlsplit

Body = bytes | Iterable[bytes] | None


class Response(Protocol):
    """The response a :class:`Transport` returns.

    An ``http.client.HTTPResponse`` already has this shape.

    Attributes:
        status: The HTTP status code.
    """

    status: int

    def read(self, amt: int | None = None, /) -> bytes:
        """Return up to ``amt`` bytes of the body, or all of the rest.

        Return ``b''`` at the end of the body.
        """
        ...

    def readline(self, limit: int = -1, /) -> bytes:
        """Return the next line of the body, or ``b''`` at the end."""
        ...

    def close(self) -> None:
        """Release the connection.

        On a streamed response, this must also be safe to call from another
        thread while a read is waiting, and must end that read.
        """
        ...


class Transport(Protocol):
    """The interface of a custom HTTP transport.

    A transport is any callable that sends one request and returns a
    :class:`Response`. Pass one to the client as ``transport=`` to add a
    proxy, tracing or a test double.
    """

    def __call__(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: Body,
        timeout: float | None,
        stream: bool,
        /,
    ) -> Response:
        """Send one request and return its response.

        Args:
            method: The HTTP method.
            url: The full URL, including the query string.
            headers: The headers to send. When ``body`` is an iterable,
                they already include its ``Content-Length``.
            body: The body as ``bytes``, as an iterable of ``bytes``
                chunks, or ``None``.
            timeout: How many seconds each connect, send or read may take.
                It is ``None`` for uploads, large file writes and the
                realtime feed, and when the client disables timeouts. Bound
                the connect yourself in that case.
            stream: Whether the caller reads the body bit by bit. The
                caller may then call ``close()`` on the response from
                another thread to stop reading.
        """
        ...


class _Buffered(io.BytesIO):
    """A response read to the end, so that its pooled connection is free."""

    def __init__(self, status: int, data: bytes) -> None:
        super().__init__(data)
        self.status = status


class _Stream:
    """A streamed response on its own connection.

    ``close()`` is safe from any thread. It shuts the socket down, which
    ends a read that is waiting.
    """

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
    # An idle keep-alive socket that turns readable was closed by the server.
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
    return ssl.create_default_context()  # Loads the CA store once (about 10 ms).


class HTTPTransport:
    """The default transport of the clients.

    It keeps one connection per thread and host, and asks for compressed
    responses on every call except the streamed ones. :meth:`close` closes
    every connection it opened.

    Args:
        timeout: How many seconds to wait for the connection on calls that
            have no timeout of their own, which are uploads, large file
            writes and the realtime feed. A streamed call also waits this
            long for the response headers. ``None`` waits forever. Do not
            pass ``0``, which makes the connection fail at once.
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
        """Send one request and return its response (see :class:`Transport`)."""
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
                pooled.close()  # It reconnects below.
            conn = pooled
            headers = {**headers, 'Accept-Encoding': 'gzip'}
        try:
            if conn.sock is None:
                conn.timeout = self.timeout if timeout is None else timeout
                conn.connect()
            sock: socket.socket = conn.sock
            if not stream:
                sock.settimeout(timeout)  # With None, an upload waits for its reply.
            conn.request(method, target, body=body, headers=headers)
            resp = conn.getresponse()
            if stream:
                sock.settimeout(timeout)  # The headers are in, so the body may idle.
                return _Stream(conn, resp, sock)
            # Read it all here: a partial read must not leave unread bytes on
            # a pooled socket, or the next request would parse them.
            data = resp.read()
            if resp.getheader('Content-Encoding') == 'gzip':
                try:
                    data = zlib.decompress(data, 47)
                except zlib.error as exc:
                    raise http.client.HTTPException(
                        f'The compressed response body is corrupt: {exc}'
                    ) from exc
            return _Buffered(resp.status, data)
        except BaseException:
            conn.close()
            raise

    def close(self) -> None:
        """Close every connection this transport opened, in every thread."""
        for conn in list(self._conns):
            conn.close()
