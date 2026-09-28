"""The default stdlib transport against a local loopback server (offline)."""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import threading
import time
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest
from helpers import APP, KEY, multipart

from squarecloud import AsyncSquareCloud, SquareCloud, SquareCloudAPIError


class Server(ThreadingHTTPServer):
    daemon_threads = True
    ports: list[int]
    headers_seen: list[dict[str, str]]
    release: threading.Event

    def handle_error(self, *_: Any) -> None:
        pass  # a client that aborts its stream (close() tests) is expected


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    server: Server

    def log_message(self, *_: Any) -> None:
        pass

    def reply(self, body: Any, status: int = 200) -> None:
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        self.server.ports.append(self.client_address[1])
        self.server.headers_seen.append(dict(self.headers))
        if self.path.endswith('/realtime'):
            if '/stall/' in self.path:
                time.sleep(1)  # slow response headers
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(b'event: logs\ndata: \x01hello\n\n')
            self.wfile.flush()
            self.server.release.wait(10)  # an idle stream
            self.close_connection = True
        elif self.path == '/snap.zip':
            data = b'S' * 300_000
            self.send_response(200)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path.endswith('/slow'):  # half a body, then a stall
            self.send_response(200)
            self.send_header('Content-Length', '40')
            self.end_headers()
            self.wfile.write(b'{"status":"success","re')
            self.wfile.flush()
            time.sleep(0.6)
            self.wfile.write(b'sponse":{"x":1}}')
        elif self.path.endswith('/gzip'):
            raw = json.dumps({'status': 'success', 'response': {'logs': 'z' * 1000}})
            packed = gzip.compress(raw.encode())
            assert 'gzip' in self.headers['Accept-Encoding']
            self.send_response(200)
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Content-Length', str(len(packed)))
            self.end_headers()
            self.wfile.write(packed)
        elif self.path.endswith('/logs'):
            self.reply({'status': 'success', 'response': {'logs': 'ok'}})
            if 'drop' in self.path:  # server closes an idle keep-alive socket
                self.close_connection = True
        else:
            self.reply({'status': 'error', 'code': 'APP_NOT_FOUND'}, 404)

    def do_POST(self) -> None:
        self.server.ports.append(self.client_address[1])
        body = self.rfile.read(int(self.headers['Content-Length']))
        if not body:
            self.reply({'status': 'success'})
            return
        [(_, filename, content)] = multipart(body, self.headers['Content-Type'])
        digest = hashlib.sha256(content).hexdigest()
        self.reply(
            {
                'status': 'success',
                'response': {'id': digest, 'name': filename},
            }
        )


@pytest.fixture
def server() -> Iterator[Server]:
    srv = Server(('127.0.0.1', 0), Handler)
    srv.ports, srv.headers_seen, srv.release = [], [], threading.Event()
    thread = threading.Thread(target=srv.serve_forever, args=(0.05,), daemon=True)
    thread.start()
    yield srv
    srv.release.set()
    srv.shutdown()
    srv.server_close()


def base(srv: Server) -> str:
    return f'http://127.0.0.1:{srv.server_address[1]}/v2'


def test_keep_alive_reuses_one_connection(server: Server) -> None:
    with SquareCloud(KEY, base_url=base(server)) as c:
        assert [c.apps.logs(APP) for _ in range(3)] == ['ok'] * 3
        with pytest.raises(SquareCloudAPIError) as info:
            c.apps.get(APP)
        assert info.value.code == 'APP_NOT_FOUND'
        assert c.apps.logs(APP) == 'ok'
    assert len(set(server.ports)) == 1
    assert server.headers_seen[0]['Authorization'] == KEY


def test_stale_keep_alive_socket_is_replaced(server: Server) -> None:
    c = SquareCloud(KEY, base_url=base(server), max_retries=0)
    assert c.apps.logs('drop') == 'ok'  # the server closes this socket
    time.sleep(0.1)
    assert c.apps.logs(APP) == 'ok'  # no RemoteDisconnected, no retry needed
    assert len(set(server.ports)) == 2
    c.close()


def test_streaming_upload_is_received_intact(server: Server, tmp_path: Path) -> None:
    data = bytes(range(256)) * 4096  # 1 MB
    zip_path = tmp_path / 'app.zip'
    zip_path.write_bytes(data)
    with SquareCloud(KEY, base_url=base(server)) as c:
        created = c.apps.create(zip_path)
    assert dict(created) == {'id': hashlib.sha256(data).hexdigest(), 'name': 'app.zip'}


def test_download_snapshot_over_http(server: Server, tmp_path: Path) -> None:
    url = f'http://127.0.0.1:{server.server_address[1]}/snap.zip'
    with SquareCloud(KEY, base_url=base(server)) as c:
        out = c.download_snapshot(url, tmp_path / 'snap.zip')
    assert Path(out).read_bytes() == b'S' * 300_000
    assert 'Authorization' not in server.headers_seen[-1]


def test_realtime_close_from_another_thread_unblocks_the_reader(server: Server) -> None:
    c = SquareCloud(KEY, base_url=base(server), timeout=0.3)
    stream = c.apps.realtime(APP)
    got: list[Any] = []
    first = threading.Event()

    def consume() -> None:
        for event in stream:
            got.append(event)
            first.set()

    reader = threading.Thread(target=consume, daemon=True)
    reader.start()
    assert first.wait(5)
    time.sleep(0.6)
    assert reader.is_alive()  # the body has no timeout: it idles past 0.3 s
    stream.close()  # the server is still holding the stream open
    reader.join(5)
    assert not reader.is_alive()
    assert got == [
        {
            'event': 'logs',
            'data': '\x01hello',
            'id': None,
            'stream': 'stdout',
            'line': 'hello',
        }
    ]


def test_realtime_headers_wait_within_the_timeout(server: Server) -> None:
    c = SquareCloud(KEY, base_url=base(server), timeout=0.3)
    with pytest.raises(SquareCloudAPIError) as info:
        list(c.apps.realtime('stall'))
    c.close()
    assert (info.value.status, info.value.code) == (0, 'TIMEOUT')


def test_async_facade_over_http(server: Server) -> None:
    async def main() -> tuple[list[str], Any]:
        async with AsyncSquareCloud(KEY, base_url=base(server)) as c:
            logs = await asyncio.gather(*(c.apps.logs(APP) for _ in range(4)))
            async with c.apps.realtime(APP) as stream:
                async for event in stream:
                    break  # leaving the block closes the idle stream
            return logs, event

    logs, event = asyncio.run(asyncio.wait_for(main(), 10))
    assert logs == ['ok'] * 4
    assert event['event'] == 'logs' and event['line'] == 'hello'


def test_partial_read_never_poisons_the_pooled_connection(server: Server) -> None:
    with SquareCloud(KEY, base_url=base(server), timeout=0.3, max_retries=0) as c:
        with pytest.raises(SquareCloudAPIError) as info:
            c.apps.get('slow')  # times out mid-body
        assert info.value.code == 'TIMEOUT'
        c.apps.start(APP)  # a mutation: must not read the stale bytes
    assert len(set(server.ports)) == 2  # it went out on a fresh connection


def test_gzip_responses_are_decoded(server: Server) -> None:
    with SquareCloud(KEY, base_url=base(server)) as c:
        assert dict(c.apps.get('gzip')) == {'logs': 'z' * 1000}
