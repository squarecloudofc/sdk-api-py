"""Streams: the realtime SSE parser and stream, multipart uploads and
snapshot downloads."""

from __future__ import annotations

import asyncio
import inspect
import io
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from helpers import APP, KEY, FakeResponse, MockTransport, client, multipart

import squarecloud.client
from squarecloud import AsyncSquareCloud, SquareCloud, SquareCloudAPIError
from squarecloud.client import _CHUNK, _multipart, _sse
from squarecloud.client import _sleep as real_sleep

# SSE parser -----------------------------------------------------------------

FEED = (
    'event: system\ndata: REALTIME_CONNECTING | abc\n\n'
    ': a comment line\n'
    'id: 7\nevent: status\n'
    'data: {"cpu":12.5,"cpuLimit":100,"ram":[128,512],"status":"running",'
    '"netIO":{"i":1},"bIO":{"i":0},"uptime":1}\n\n'
    'event: status\ndata: {"cpu":13.1,"ram":[131,512],'
    '"netIO":{"i":2},"bIO":{"i":0}}\n\n'
    'event: logs\ndata: \x01Server listening on :3000\n\n'
    'event: logs\r\ndata:\x02Error: boom\r\n\r\n'
    'event: logs\ndata: no prefix\n\n'
    'event: logs\ndata: \x01line one\ndata: line two\n\n'
    'event: error\ndata: CONTAINER_NOT_FOUND\n\n'
)


def events(text: str) -> list[tuple[str, str, str | None]]:
    return list(_sse(FakeResponse(200, text.encode())))


def test_parser_fields_spaces_comments_and_multiline() -> None:
    parsed = events('event: a\ndata:  two spaces\ndata:x\nid:9\n\ndata: plain\n\n')
    assert parsed == [('a', ' two spaces\nx', '9'), ('message', 'plain', '9')]


def test_parser_strips_one_cr_and_ignores_retry_and_unknown_fields() -> None:
    parsed = events('retry: 10\nfoo: bar\ndata: a\r\r\n\r\n')
    assert parsed == [('message', 'a\r', None)]


def test_parser_discards_an_unterminated_frame_at_eof() -> None:
    assert events('event: logs\ndata: tail') == []
    assert events('data: a\n\ndata: b\n') == [('message', 'a', None)]


def test_parser_ignores_ids_with_nul() -> None:
    parsed = events('id: 1\ndata: a\n\nid: x\0y\ndata: b\n\n')
    assert parsed == [('message', 'a', '1'), ('message', 'b', '1')]


def test_parser_empty_data_line_dispatches_empty_string() -> None:
    assert events('event: system\ndata:\n\n') == [('system', '', None)]


def test_parser_blank_line_without_data_dispatches_nothing() -> None:
    assert events('event: logs\n\n\n') == []


def test_parser_empty_event_field_is_a_message() -> None:
    assert events('event:\ndata: a\n\n') == [('message', 'a', None)]


# Realtime stream ------------------------------------------------------------


def test_realtime_decodes_logs_and_merges_status() -> None:
    c, t = client(FakeResponse(200, FEED))
    got: list[Any] = list(c.apps.realtime(APP))
    assert got[0] == {
        'event': 'system',
        'data': 'REALTIME_CONNECTING | abc',
        'id': None,
    }
    assert got[2]['data'] == (
        '{"cpu":13.1,"ram":[131,512],"netIO":{"i":2},"bIO":{"i":0}}'
    )  # data stays the raw frame
    full, lean = got[1]['status'], got[2]['status']
    assert full['status'] == 'running' and full['cpu'] == 12.5
    assert lean == {
        'cpu': 13.1,
        'cpuLimit': 100,
        'ram': [131, 512],
        'status': 'running',
        'netIO': {'i': 2},
        'bIO': {'i': 0},
        'uptime': 1,
    }
    assert got[1]['id'] == '7'
    assert full['cpu'] == 12.5  # earlier events are not mutated by later merges
    assert [(e['stream'], e['line']) for e in got[3:7]] == [
        ('stdout', 'Server listening on :3000'),
        ('stderr', 'Error: boom'),
        ('stdout', 'no prefix'),
        ('stdout', 'line one\nline two'),
    ]
    assert got[4] == {
        'event': 'logs',
        'data': '\x02Error: boom',
        'id': '7',
        'stream': 'stderr',
        'line': 'Error: boom',
    }
    assert got[7] == {'event': 'error', 'data': 'CONTAINER_NOT_FOUND', 'id': '7'}
    call = t.calls[0]
    assert (
        call.stream
        and call.timeout is None
        and call.headers['Accept'] == 'text/event-stream'
    )


def test_malformed_status_keeps_the_last_state() -> None:
    feed = (
        'event: status\ndata: {"cpu":1}\n\n'
        'event: status\ndata: not json\n\n'
        'event: status\ndata: [1]\n\n'
    )
    c, _ = client(FakeResponse(200, feed))
    assert [e['status'] for e in c.apps.realtime(APP)] == [{'cpu': 1}] * 3  # type: ignore[typeddict-item]


def test_realtime_checks_status_before_streaming() -> None:
    body = {'status': 'error', 'code': 'REALTIME_MAX_CONNECTIONS', 'message': 'max 5'}
    c, _ = client(FakeResponse(429, body))
    with pytest.raises(SquareCloudAPIError) as info:
        list(c.apps.realtime(APP))
    assert (info.value.status, info.value.code) == (429, 'REALTIME_MAX_CONNECTIONS')


def test_realtime_stops_on_disconnected() -> None:
    feed = 'event: system\ndata: REALTIME_DISCONNECTED\n\nevent: logs\ndata: never\n\n'
    c, t = client(FakeResponse(200, feed))
    assert [e['data'] for e in c.apps.realtime(APP)] == ['REALTIME_DISCONNECTED']
    assert len(t.calls) == 1


class Dropping(FakeResponse):
    """Delivers its frames, then fails like a connection reset."""

    def readline(self, limit: int = -1, /) -> bytes:
        line = super().readline(limit)
        if not line:
            raise ConnectionResetError('reset')
        return line


def test_realtime_reconnects_after_network_error() -> None:
    c, t = client(
        Dropping(200, 'event: logs\ndata: a\n\n'),
        FakeResponse(200, 'event: logs\ndata: b\n\n'),
    )
    assert [e.get('line') for e in c.apps.realtime(APP)] == ['a', 'b']
    assert len(t.calls) == 2


def test_realtime_gives_up_after_three_reconnects() -> None:
    c, t = client(*[Dropping(200, '') for _ in range(4)])
    with pytest.raises(SquareCloudAPIError) as info:
        list(c.apps.realtime(APP))
    assert (info.value.status, info.value.code) == (0, 'NETWORK_ERROR')
    assert isinstance(info.value.cause, ConnectionResetError)
    assert len(t.calls) == 4


def test_realtime_system_events_do_not_reset_the_reconnect_budget() -> None:
    connecting = 'event: system\ndata: REALTIME_CONNECTING | x\n\n'
    c, t = client(*[Dropping(200, connecting) for _ in range(5)])
    with pytest.raises(SquareCloudAPIError) as info:
        list(c.apps.realtime(APP))
    assert (info.value.code, info.value.path) == (
        'NETWORK_ERROR',
        f'/v2/apps/{APP}/realtime',
    )
    assert len(t.calls) == 4


@pytest.mark.parametrize(
    'frame', ['event: logs\ndata: x\n\n', 'event: status\ndata: {}\n\n']
)
def test_realtime_log_and_status_events_reset_the_reconnect_budget(
    frame: str,
) -> None:
    c, t = client(*[Dropping(200, frame) for _ in range(5)], FakeResponse(200, ''))
    assert len(list(c.apps.realtime(APP))) == 5
    assert len(t.calls) == 6


def test_realtime_status_merge_survives_a_reconnect() -> None:
    c, _ = client(
        Dropping(200, 'event: status\ndata: {"cpu":1,"ram":2}\n\n'),
        FakeResponse(200, 'event: status\ndata: {"cpu":3}\n\n'),
    )
    got = [e['status'] for e in c.apps.realtime(APP)]  # type: ignore[typeddict-item]
    assert got == [{'cpu': 1, 'ram': 2}, {'cpu': 3, 'ram': 2}]


def test_realtime_reopens_on_server_reconnect_at_the_api_pace(
    sleeps: list[float],
) -> None:
    c, t = client(
        FakeResponse(
            200, 'event: logs\ndata: a\n\nevent: system\ndata: REALTIME_RECONNECT\n\n'
        ),
        FakeResponse(200, 'event: logs\ndata: b\n\n'),
    )
    got = [e['data'] for e in c.apps.realtime(APP)]
    assert got == ['a', 'REALTIME_RECONNECT', 'b']
    assert len(t.calls) == 2
    assert len(sleeps) == 1 and 5.4 <= sleeps[0] <= 5.5  # one open per 5 s per app


def test_realtime_reopen_is_a_get_under_max_retries(sleeps: list[float]) -> None:
    c, t = client(
        Dropping(200, 'event: logs\ndata: a\n\n'),
        ConnectionRefusedError('refused'),
        FakeResponse(200, 'event: logs\ndata: b\n\n'),
    )
    assert [e.get('line') for e in c.apps.realtime(APP)] == ['a', 'b']
    assert len(t.calls) == 3
    assert sleeps[0] >= 5.4 and 0.25 <= sleeps[1] <= 0.5  # pace, then GET backoff


def test_realtime_open_error_on_reopen_is_raised() -> None:
    c, t = client(
        Dropping(200, 'event: logs\ndata: a\n\n'),
        ConnectionRefusedError('refused'),
        max_retries=0,
    )
    with pytest.raises(SquareCloudAPIError) as info:
        list(c.apps.realtime(APP))
    assert (info.value.status, info.value.code) == (0, 'NETWORK_ERROR')
    assert len(t.calls) == 2


def test_realtime_http_error_on_reopen_is_raised() -> None:
    c, t = client(
        Dropping(200, 'event: logs\ndata: a\n\n'),
        FakeResponse(429, {'status': 'error', 'code': 'KEEP_CALM'}),
    )
    with pytest.raises(SquareCloudAPIError) as info:
        list(c.apps.realtime(APP))
    assert info.value.code == 'KEEP_CALM'
    assert len(t.calls) == 2


def test_realtime_endless_server_reconnects_give_up() -> None:
    feed = 'event: system\ndata: REALTIME_RECONNECT\n\n'
    c, t = client(*[FakeResponse(200, feed) for _ in range(5)])
    with pytest.raises(SquareCloudAPIError) as info:
        list(c.apps.realtime(APP))
    assert info.value.code == 'NETWORK_ERROR'
    assert len(t.calls) == 4


def test_realtime_close_after_a_server_reconnect_ends_quietly() -> None:
    feed = 'event: system\ndata: REALTIME_RECONNECT\n\n'
    stream: Any = None

    class Closing(FakeResponse):
        """Ends like a socket shut down by ``close()`` from another thread."""

        def readline(self, limit: int = -1, /) -> bytes:
            line = super().readline(limit)
            if not line:
                stream.close()
            return line

    c, t = client(*[FakeResponse(200, feed) for _ in range(3)], Closing(200, feed))
    stream = c.apps.realtime(APP)
    assert len(list(stream)) == 4  # no NETWORK_ERROR: the caller closed it
    assert len(t.calls) == 4


def test_realtime_close_stops_iteration_and_closes_response() -> None:
    resp = FakeResponse(200, FEED)
    c, _ = client(resp)
    with c.apps.realtime(APP) as stream:
        for event in stream:
            assert event['event'] == 'system'
            break
    assert resp.closed


def test_realtime_close_during_the_reopen_wait_ends_at_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(squarecloud.client, '_sleep', real_sleep)
    c, t = client(
        Dropping(200, 'event: logs\ndata: a\n\n'),
        FakeResponse(200, 'event: logs\ndata: b\n\n'),
    )
    stream = c.apps.realtime(APP)
    timer = threading.Timer(0.2, stream.close)
    start = time.monotonic()
    timer.start()
    assert [e['data'] for e in stream] == ['a']  # never waits the 5.5 s
    assert time.monotonic() - start < 3
    assert len(t.calls) == 1


def test_realtime_close_while_connecting_ends_the_stream() -> None:
    resp = FakeResponse(200, FEED)
    transport = MockTransport()
    stream = SquareCloud(KEY, transport=transport).apps.realtime(APP)

    def connect(_: Any) -> FakeResponse:
        stream.close()  # lands while the open is in flight
        return resp

    transport.handler = connect
    assert list(stream) == []
    assert resp.closed


def test_realtime_close_during_the_open_retry_wait_ends_at_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(squarecloud.client, '_sleep', real_sleep)
    transport = MockTransport(handler=lambda _: ConnectionRefusedError('refused'))
    stream = SquareCloud(KEY, transport=transport, max_retries=10).apps.realtime(APP)
    timer = threading.Timer(0.2, stream.close)
    start = time.monotonic()
    timer.start()
    assert list(stream) == []  # quiet, and never the whole ~40 s of backoff
    assert time.monotonic() - start < 3
    assert len(transport.calls) <= 2


def test_async_realtime() -> None:
    async def main() -> list[str]:
        transport = MockTransport([FakeResponse(200, FEED)])
        async with AsyncSquareCloud(KEY, transport=transport) as c:
            return [e['event'] async for e in c.apps.realtime(APP)]

    assert asyncio.run(main()) == [
        'system',
        'status',
        'status',
        'logs',
        'logs',
        'logs',
        'logs',
        'error',
    ]


def test_async_realtime_propagates_errors() -> None:
    async def main() -> None:
        transport = MockTransport(
            [FakeResponse(429, {'status': 'error', 'code': 'REALTIME_MAX_CONNECTIONS'})]
        )
        async for _ in AsyncSquareCloud(KEY, transport=transport).apps.realtime(APP):
            pass

    with pytest.raises(SquareCloudAPIError):
        asyncio.run(main())


# Multipart uploads ----------------------------------------------------------


def parse(body: bytes, content_type: str) -> tuple[str | None, bytes]:
    [(name, filename, content)] = multipart(body, content_type)
    assert name == 'file'
    return filename, content


def test_path_is_streamed_in_chunks_with_exact_length(tmp_path: Path) -> None:
    data = bytes(range(256)) * 1000  # 256 KB, binary
    zip_path = tmp_path / 'my bot.zip'
    zip_path.write_bytes(data)
    factory, headers = _multipart(zip_path, '/apps')
    chunks = list(factory())
    body = b''.join(chunks)
    assert int(headers['Content-Length']) == len(body)
    assert max(len(c) for c in chunks[1:-1]) <= _CHUNK  # never the whole file
    assert parse(body, headers['Content-Type']) == ('my bot.zip', data)


def test_factory_reopens_the_file_each_attempt(tmp_path: Path) -> None:
    zip_path = tmp_path / 'a.zip'
    zip_path.write_bytes(b'PK123')
    factory, _ = _multipart(str(zip_path), '/apps')
    assert b''.join(factory()) == b''.join(factory())


def test_bytes_and_file_objects() -> None:
    factory, headers = _multipart(b'PKbytes', '/apps')
    assert parse(b''.join(factory()), headers['Content-Type']) == (
        'app.zip',
        b'PKbytes',
    )

    fobj = io.BytesIO(b'skipPKfile')
    fobj.seek(4)  # uploads from the current position
    factory, headers = _multipart(fobj, '/apps')
    first, second = b''.join(factory()), b''.join(factory())
    assert first == second
    assert int(headers['Content-Length']) == len(first)
    assert parse(first, headers['Content-Type'])[1] == b'PKfile'


def test_non_seekable_stream_is_buffered_once() -> None:
    class Pipe(io.RawIOBase):
        def __init__(self) -> None:
            self.data = io.BytesIO(b'PKpipe')

        def readable(self) -> bool:
            return True

        def readinto(self, b: bytearray) -> int:  # type: ignore[override]
            n = self.data.readinto(b)
            return n

    factory, headers = _multipart(io.BufferedReader(Pipe()), '/apps')  # type: ignore[type-var]
    body = b''.join(factory())
    assert parse(body, headers['Content-Type'])[1] == b'PKpipe'
    assert int(headers['Content-Length']) == len(body)


def test_filename_is_sanitized() -> None:
    fobj = io.BytesIO(b'PK')
    fobj.name = 'we"ird\r\nname.zip'
    factory, _ = _multipart(fobj, '/apps')
    head = next(iter(factory()))
    assert b'filename="we%22irdname.zip"' in head


def test_zip_over_100mb_fails_before_sending(tmp_path: Path) -> None:
    big = tmp_path / 'big.zip'
    with open(big, 'wb') as f:
        f.truncate(100 * 1024 * 1024 + 1)  # sparse
    c, t = client()
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.create(big)
    assert (info.value.status, info.value.code) == (0, 'FILE_TOO_LARGE')
    assert info.value.path == '/v2/apps'
    assert t.calls == []


def test_commit_sends_multipart_and_path_query(tmp_path: Path) -> None:
    zip_path = tmp_path / 'c.zip'
    zip_path.write_bytes(b'PKcommit')
    c, t = client(FakeResponse(200))
    c.apps.commit(APP, zip_path, path='/src')
    call = t.calls[0]
    assert call.headers['Content-Type'].startswith('multipart/form-data; boundary=')
    assert int(call.headers['Content-Length']) == len(call.body or b'')
    assert call.chunks is not None and len(call.chunks) == 3
    assert call.query == {'path': ['/src']}
    assert call.timeout is None  # uploads have no timeout
    assert parse(call.body or b'', call.headers['Content-Type']) == (
        'c.zip',
        b'PKcommit',
    )


def test_unnamed_uploads_get_the_default_names() -> None:
    c, t = client(
        FakeResponse(200), FakeResponse(200, {'status': 'success', 'response': {}})
    )
    c.apps.commit(APP, b'PK')
    c.apps.create(b'PK')
    names = [parse(x.body or b'', x.headers['Content-Type'])[0] for x in t.calls]
    assert names == ['commit.zip', 'app.zip']


def test_commit_filename_names_a_single_file() -> None:
    c, t = client(FakeResponse(200))
    c.apps.commit(APP, b'print(1)', path='/src', filename='main.py')
    assert parse(t.calls[0].body or b'', t.calls[0].headers['Content-Type']) == (
        'main.py',
        b'print(1)',
    )


def test_upload_busy_retries_post_and_restreams_body(tmp_path: Path) -> None:
    zip_path = tmp_path / 'bot.zip'
    zip_path.write_bytes(b'PK' + b'z' * 200_000)
    created = {'status': 'success', 'response': {'id': APP}}
    c, t = client(
        FakeResponse(503, {'status': 'error', 'code': 'UPLOAD_BUSY'}),
        FakeResponse(200, created),
    )
    assert c.apps.create(zip_path)['id'] == APP
    assert len(t.calls) == 2
    assert t.calls[0].body == t.calls[1].body
    assert b'PK' + b'z' * 200_000 in (t.calls[1].body or b'')


def test_failed_upload_closes_the_file(tmp_path: Path) -> None:
    zip_path = tmp_path / 'a.zip'
    zip_path.write_bytes(b'PK' * 100)
    bodies: list[Any] = []

    def reset(*args: Any) -> FakeResponse:
        body = args[3]
        bodies.append(body)
        next(body), next(body)  # the head, then a chunk: the file is open
        raise ConnectionResetError('reset')

    c, _ = client()
    c._transport = reset
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.create(zip_path)
    # The traceback in `info` still references the body: it must be closed.
    assert info.value.code == 'NETWORK_ERROR'
    assert inspect.getgeneratorstate(bodies[0]) == inspect.GEN_CLOSED


def test_missing_or_directory_upload_raises_oserror(tmp_path: Path) -> None:
    c, t = client()
    with pytest.raises(FileNotFoundError):
        c.apps.create(tmp_path / 'nope.zip')
    with pytest.raises(OSError) as info:
        c.apps.create(tmp_path)
    assert not isinstance(info.value, SquareCloudAPIError)
    assert t.calls == []


def test_upload_file_that_shrinks_fails_instead_of_hanging(tmp_path: Path) -> None:
    zip_path = tmp_path / 'a.zip'
    zip_path.write_bytes(b'PK' * 100)
    c, t = client(FakeResponse(200))

    def shrinking(*args: Any) -> FakeResponse:
        zip_path.write_bytes(b'PK')  # truncated after the size was taken
        return t(*args)

    c._transport = shrinking
    with pytest.raises(OSError, match='shrank'):
        c.apps.commit(APP, zip_path)


# Snapshot download ----------------------------------------------------------

SNAP = 'https://snapshots.squarecloud.app/u/app.zip?sig=1'


class Broken(FakeResponse):
    """Delivers the first chunk, then fails mid-body."""

    def read(self, amt: int | None = None, /) -> bytes:
        if self._buf.tell():
            raise ConnectionResetError('reset')
        return super().read(amt)


def test_download_snapshot_streams_to_file_without_the_key(tmp_path: Path) -> None:
    c, t = client(FakeResponse(200, b'Z' * 200_000), user_agent='probe/1')
    out = c.download_snapshot(SNAP, tmp_path)
    assert Path(out) == tmp_path / 'app.zip'
    assert Path(out).read_bytes() == b'Z' * 200_000
    call = t.calls[0]
    assert call.stream and call.headers == {'User-Agent': 'probe/1'}
    assert call.timeout == c._timeout  # unlike realtime, every read is bounded
    assert call.url == SNAP


def test_download_snapshot_retries_a_network_error(tmp_path: Path) -> None:
    c, t = client(ConnectionResetError('reset'), FakeResponse(200, b'Z'))
    assert Path(c.download_snapshot(SNAP, tmp_path)).read_bytes() == b'Z'
    assert len(t.calls) == 2


def test_download_snapshot_error_leaves_no_file(tmp_path: Path) -> None:
    c, _ = client(FakeResponse(403, b'<Error>AccessDenied</Error>'))
    with pytest.raises(SquareCloudAPIError) as info:
        c.download_snapshot(SNAP, tmp_path / 'x.zip')
    e = info.value
    assert (e.status, e.code, e.message, e.path) == (
        403,
        'UNKNOWN_ERROR',
        'HTTP 403',
        '/u/app.zip',  # never the presigned query
    )
    assert list(tmp_path.iterdir()) == []


def test_download_snapshot_midstream_failure_keeps_the_previous_file(
    tmp_path: Path,
) -> None:
    old = tmp_path / 'x.zip'
    old.write_bytes(b'previous backup')
    c, _ = client(Broken(200, b'Z' * 10))
    with pytest.raises(SquareCloudAPIError) as info:
        c.download_snapshot(SNAP, old)
    assert info.value.code == 'NETWORK_ERROR'
    assert old.read_bytes() == b'previous backup'
    assert list(tmp_path.iterdir()) == [old]


def test_download_snapshot_creates_a_directory_dest(tmp_path: Path) -> None:
    c, _ = client(FakeResponse(200, b'Z'))
    out = c.download_snapshot(SNAP, f'{tmp_path}/backups/')
    assert Path(out) == tmp_path / 'backups' / 'app.zip'
    assert Path(out).read_bytes() == b'Z'
