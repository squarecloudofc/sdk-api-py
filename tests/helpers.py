"""Offline test doubles: a scripted transport and an in-memory response."""

from __future__ import annotations

import email.parser
import io
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, cast
from urllib.parse import parse_qs, urlsplit

from squarecloud import SquareCloud

APP = '0123456789abcdef0123456789abcdef'
DB = 'fedcba9876543210fedcba9876543210'
WS = 'aaaaaaaabbbb4bbb8cccccccdddddddd'  # a hyphenless uuid v4 (or 40 hex)
KEY = 'test-key-' + 'x' * 60


class FakeResponse:
    def __init__(self, status: int = 200, body: Any = None) -> None:
        if body is None:
            body = {'status': 'success'}
        raw = (
            body
            if isinstance(body, bytes)
            else (body.encode() if isinstance(body, str) else json.dumps(body).encode())
        )
        self.status = status
        self._buf = io.BytesIO(raw)
        self.closed = False

    def read(self, amt: int | None = None, /) -> bytes:
        return self._buf.read(-1 if amt is None else amt)

    def readline(self, limit: int = -1, /) -> bytes:
        return self._buf.readline(limit)

    def close(self) -> None:
        self.closed = True


@dataclass
class Call:
    method: str
    url: str
    headers: dict[str, str]
    body: bytes | None
    chunks: list[bytes] | None
    timeout: float | None
    stream: bool

    @property
    def path(self) -> str:
        return urlsplit(self.url).path

    @property
    def query(self) -> dict[str, list[str]]:
        return parse_qs(urlsplit(self.url).query, keep_blank_values=True)

    def json(self) -> Any:
        assert self.body is not None
        return json.loads(self.body)


Reply = FakeResponse | BaseException


@dataclass
class MockTransport:
    """Answers with ``handler(call)`` or, when absent, pops ``replies``."""

    replies: list[Reply] = field(default_factory=list)
    handler: Callable[[Call], Reply] | None = None
    calls: list[Call] = field(default_factory=list)

    def __call__(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: bytes | Iterable[bytes] | None,
        timeout: float | None,
        stream: bool,
    ) -> FakeResponse:
        chunks = None
        if body is not None and not isinstance(body, bytes):
            chunks = list(body)
            body = b''.join(chunks)
        call = Call(method, url, dict(headers), body, chunks, timeout, stream)
        self.calls.append(call)
        reply = self.handler(call) if self.handler else self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply


def client(*replies: Reply, **kwargs: Any) -> tuple[SquareCloud, MockTransport]:
    transport = MockTransport(list(replies))
    return SquareCloud(KEY, transport=transport, **kwargs), transport


def multipart(body: bytes, content_type: str) -> list[tuple[str, str | None, bytes]]:
    """(field name, filename, content) of each part, via the stdlib parser."""
    raw = f'Content-Type: {content_type}\r\n\r\n'.encode() + body
    parts = cast(list[Any], email.parser.BytesParser().parsebytes(raw).get_payload())
    return [
        (
            p.get_param('name', header='content-disposition'),
            p.get_filename(),
            p.get_payload(decode=True),
        )
        for p in parts
    ]
