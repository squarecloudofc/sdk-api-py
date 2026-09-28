"""(a) Transport: errors, 202 pending, retry rules, timeouts, URL escaping."""

from __future__ import annotations

import asyncio
import base64
import http.client
import pickle
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from helpers import APP, DB, KEY, Call, FakeResponse, MockTransport, client

from squarecloud import (
    AsyncSquareCloud,
    HTTPTransport,
    SquareCloud,
    SquareCloudAPIError,
    __version__,
)


def err(status: int, code: str, message: str = '') -> FakeResponse:
    return FakeResponse(status, {'status': 'error', 'code': code, 'message': message})


# Errors ---------------------------------------------------------------------


def test_api_error_carries_status_code_message_method_path() -> None:
    c, _ = client(err(404, 'APP_NOT_FOUND', 'nope'))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.get(APP)
    e = info.value
    assert (e.status, e.code, e.message, e.method) == (
        404,
        'APP_NOT_FOUND',
        'nope',
        'GET',
    )
    assert e.path == f'/v2/apps/{APP}'
    assert e.cause is None
    assert str(e) == f'GET /v2/apps/{APP}: HTTP 404 APP_NOT_FOUND: nope'
    clone = pickle.loads(pickle.dumps(e))
    assert (clone.status, clone.code, clone.message) == (404, 'APP_NOT_FOUND', 'nope')


@pytest.mark.parametrize(
    'code', ['MISSING_SCOPE', 'RESOURCE_NOT_ALLOWED', 'BLOCKED_PATH']
)
def test_403_codes_surface_verbatim(code: str) -> None:
    c, _ = client(err(403, code))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.files.delete(APP, '/old.js')
    assert info.value.code == code


def test_expired_key_is_access_denied() -> None:
    c, _ = client(err(401, 'ACCESS_DENIED', 'This credential was not recognized.'))
    with pytest.raises(SquareCloudAPIError) as info:
        c.account.me()
    assert (info.value.status, info.value.code) == (401, 'ACCESS_DENIED')


def test_str_omits_status_0_and_an_empty_message() -> None:
    e = SquareCloudAPIError(0, 'TIMEOUT', 'timed out', 'GET', '/v2/x')
    assert str(e) == 'GET /v2/x: TIMEOUT: timed out'
    e = SquareCloudAPIError(400, 'GIT_NOT_CONFIGURED', '', 'DELETE', '/v2/y')
    assert str(e) == 'DELETE /v2/y: HTTP 400 GIT_NOT_CONFIGURED'


def test_code_without_message_has_an_empty_message() -> None:
    c, _ = client(err(400, 'GIT_NOT_CONFIGURED'))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.deploys.unlink_github_app(APP)
    assert (info.value.code, info.value.message) == ('GIT_NOT_CONFIGURED', '')


def test_non_2xx_without_code_raises() -> None:
    c, _ = client(FakeResponse(500, {'status': 'error'}))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.logs(APP)
    e = info.value
    assert (e.status, e.code, e.message) == (500, 'UNKNOWN_ERROR', 'HTTP 500')


def test_non_json_error_body_is_not_a_transport_leak() -> None:
    c, t = client(FakeResponse(502, b'<html>Bad gateway</html>'))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.get(APP)
    e = info.value
    assert (e.status, e.code, e.message, e.cause) == (
        502,
        'UNKNOWN_ERROR',
        'HTTP 502',
        None,
    )
    assert len(t.calls) == 1  # 502 is never retried


def test_non_json_success_body_raises() -> None:
    c, _ = client(FakeResponse(200, b'not json'))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.get(APP)
    e = info.value
    assert (e.status, e.code, e.message) == (
        200,
        'UNKNOWN_ERROR',
        'Invalid JSON in HTTP 200 response',
    )
    assert isinstance(e.cause, ValueError)


def test_empty_2xx_body_is_success() -> None:
    c, _ = client(FakeResponse(200, b''), FakeResponse(200, b''))
    c.apps.start(APP)
    assert c.apps.deploys.current(APP) == {}


def test_ai_openai_dialect_error() -> None:
    body = {
        'error': {
            'message': 'slow down',
            'type': 'rate_limit_error',
            'code': 'rate_limit_exceeded',
        }
    }
    c, t = client(FakeResponse(429, body))
    with pytest.raises(SquareCloudAPIError) as info:
        c.ai.chat({'messages': [{'role': 'user', 'content': 'hi'}]})
    assert (info.value.status, info.value.code, info.value.message) == (
        429,
        'rate_limit_exceeded',
        'slow down',
    )
    assert len(t.calls) == 1


@pytest.mark.parametrize(
    ('status', 'code', 'kind'),
    [
        (401, 'access_denied', 'authentication_error'),
        (403, 'missing_scope', 'invalid_request_error'),
        (429, 'rate_limited', 'rate_limit_error'),
        (503, 'database_unavailable', 'server_error'),
    ],
)
def test_ai_errors_keep_the_lowercase_openai_code(
    status: int, code: str, kind: str
) -> None:
    body = {'error': {'message': 'm', 'type': kind, 'param': None, 'code': code}}
    c, t = client(FakeResponse(status, body))
    with pytest.raises(SquareCloudAPIError) as info:
        c.ai.chat({'messages': [{'role': 'user', 'content': 'hi'}]})
    assert (info.value.status, info.value.code, info.value.message) == (
        status,
        code,
        'm',
    )
    assert len(t.calls) == 1  # a POST: not even database_unavailable retries


def test_ai_square_dialect_error() -> None:
    c, _ = client(err(403, 'MISSING_SCOPE'))
    with pytest.raises(SquareCloudAPIError) as info:
        c.ai.chat({'messages': [{'role': 'user', 'content': 'hi'}]})
    assert info.value.code == 'MISSING_SCOPE'


# 202 pending ----------------------------------------------------------------


@pytest.mark.parametrize('group', ['apps', 'databases'])
def test_snapshot_202_is_pending_not_error(group: str) -> None:
    c, _ = client(
        FakeResponse(202, {'status': 'error', 'code': 'SNAPSHOT_PROCESSING'}),
        FakeResponse(
            200,
            {'status': 'success', 'response': {'url': 'https://s/x.zip', 'key': 'k'}},
        ),
    )
    snapshots = getattr(c, group).snapshots
    assert snapshots.create(APP) == {'pending': True}
    assert snapshots.create(APP) == {
        'pending': False,
        'url': 'https://s/x.zip',
        'key': 'k',
    }


# Retries --------------------------------------------------------------------


def test_get_retries_network_errors_with_backoff(sleeps: list[float]) -> None:
    c, t = client(
        ConnectionResetError('reset'),
        http.client.RemoteDisconnected('gone'),
        FakeResponse(200, {'status': 'success', 'response': {'logs': 'ok'}}),
    )
    assert c.apps.logs(APP) == 'ok'
    assert len(t.calls) == 3
    assert 0.25 <= sleeps[0] <= 0.5 and 0.5 <= sleeps[1] <= 1.0


def test_backoff_is_capped_at_8_seconds(sleeps: list[float]) -> None:
    c, _ = client(*[ConnectionResetError('reset')] * 7, max_retries=6)
    with pytest.raises(SquareCloudAPIError):
        c.apps.get(APP)
    assert len(sleeps) == 6 and max(sleeps) <= 8.0 and sleeps[-1] >= 4.0


def test_get_gives_up_after_max_retries() -> None:
    c, t = client(*[ConnectionResetError('reset')] * 3)
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.get(APP)
    assert (info.value.status, info.value.code) == (0, 'NETWORK_ERROR')
    assert isinstance(info.value.cause, ConnectionResetError)
    assert len(t.calls) == 3


@pytest.mark.parametrize('max_retries', [0, -1])
def test_max_retries_zero_or_less_disables_retries(max_retries: int) -> None:
    c, t = client(ConnectionResetError('reset'), max_retries=max_retries)
    with pytest.raises(SquareCloudAPIError):
        c.apps.get(APP)
    assert len(t.calls) == 1


@pytest.mark.parametrize(
    'exc',
    [
        ConnectionResetError('reset'),
        http.client.RemoteDisconnected('gone'),
        http.client.IncompleteRead(b''),  # an HTTPException that is no OSError
    ],
)
def test_mutations_never_retry_network_errors(exc: BaseException) -> None:
    c, t = client(exc)
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.restart(APP)
    assert info.value.code == 'NETWORK_ERROR'
    assert len(t.calls) == 1


def test_timeout_is_never_retried() -> None:
    c, t = client(TimeoutError('timed out'))  # max_retries=2, GET
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.get(APP)
    assert (info.value.status, info.value.code) == (0, 'TIMEOUT')
    assert len(t.calls) == 1


def test_calls_the_server_holds_open_wait_longer() -> None:
    c, t = client(timeout=7)
    t.handler = lambda _: FakeResponse(200)
    c.apps.start(APP)
    c.apps.stop(APP)
    c.apps.restart(APP)
    c.databases.start(DB)
    c.databases.stop(DB)
    c.databases.create('db', type='redis', version='7', memory=256)
    c.apps.snapshots.create(APP)
    c.databases.snapshots.restore(DB, 'n', 'v')
    c.ai.chat({'messages': []})
    c.apps.get(APP)
    assert [x.timeout for x in t.calls] == [120] * 9 + [7]  # AI included
    c2, t2 = client(FakeResponse(200), timeout=900)
    c2.apps.start(APP)
    assert t2.calls[0].timeout == 900  # never lowered


@pytest.mark.parametrize('timeout', [0, -1])
def test_timeout_0_or_less_disables_every_timeout(timeout: float) -> None:
    c, t = client(timeout=timeout)
    t.handler = lambda _: FakeResponse(200)
    c.apps.get(APP)
    c.apps.start(APP)
    c.ai.chat({'messages': []})
    assert [x.timeout for x in t.calls] == [None] * 3
    default = SquareCloud(KEY, timeout=timeout)._transport
    assert isinstance(default, HTTPTransport) and default.timeout is None


def test_files_write_over_1mib_has_no_timeout() -> None:
    c, t = client(FakeResponse(200), FakeResponse(200))
    c.apps.files.write(APP, '/a', 'x' * (1024 * 1024))
    c.apps.files.write(APP, '/b', b'\xff' * (1024 * 1024 + 1))
    assert [x.timeout for x in t.calls] == [30.0, None]


@pytest.mark.parametrize(
    'call',
    [
        lambda c: c.databases.start(DB),
        lambda c: c.apps.start(APP),
        lambda c: c.apps.envs.get(APP),
    ],
)
def test_2xx_error_envelope_raises(call: Any) -> None:
    c, _ = client(err(200, 'DATABASE_START_FAILED', 'cluster said no'))
    with pytest.raises(SquareCloudAPIError) as info:
        call(c)
    assert (info.value.status, info.value.code) == (200, 'DATABASE_START_FAILED')


def test_unenveloped_routes_skip_the_envelope_check() -> None:
    c, _ = client(FakeResponse(200, {'status': 'error', 'message': 'degraded'}))
    assert c.service.status()['status'] == 'error'


@pytest.mark.parametrize('bad', ['', '.', '..'])
def test_dot_or_empty_ids_fail_locally(bad: str) -> None:
    c, t = client()
    for call in (lambda: c.apps.status(bad), lambda: c.workspaces.get(bad)):
        with pytest.raises(SquareCloudAPIError) as info:
            call()
        assert (info.value.status, info.value.code) == (0, 'INVALID_ID')
    assert t.calls == []


def test_analytics_busy_retries() -> None:
    c, t = client(
        err(503, 'ANALYTICS_BUSY'),
        FakeResponse(200, {'status': 'success', 'response': []}),
    )
    assert (
        c.apps.network.logs(APP, '2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z') == []
    )
    assert len(t.calls) == 2


def test_database_unavailable_retries_only_get() -> None:
    c, t = client(
        err(503, 'DATABASE_UNAVAILABLE'),
        FakeResponse(200, {'status': 'success', 'response': []}),
    )
    assert c.apps.metrics(APP) == []
    assert len(t.calls) == 2
    c, t = client(err(503, 'DATABASE_UNAVAILABLE'))
    with pytest.raises(SquareCloudAPIError):
        c.apps.start(APP)
    assert len(t.calls) == 1


@pytest.mark.parametrize(
    'code', ['RATE_LIMITED', 'KEEP_CALM', 'RATE_LIMIT', 'RATE_LIMIT_EXCEEDED']
)
def test_429_is_never_retried(code: str) -> None:
    c, t = client(err(429, code))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.get(APP)
    assert info.value.code == code
    assert len(t.calls) == 1


def test_ai_server_overloaded_is_not_retried() -> None:
    body = {'error': {'code': 'server_overloaded', 'type': 'server_error'}}
    c, t = client(FakeResponse(503, body))
    with pytest.raises(SquareCloudAPIError) as info:
        c.ai.chat({'messages': []})
    assert (info.value.status, info.value.code) == (503, 'server_overloaded')
    assert len(t.calls) == 1


@pytest.mark.parametrize(
    'code',
    [
        'CONTAINER_ALREADY_STARTED',
        'CONTAINER_ALREADY_STOPPED',
        'CONTAINER_TEMPORARILY_SUSPENDED',
        'ACTION_FAILED',
    ],
)
@pytest.mark.parametrize('action', ['start', 'stop'])
def test_database_start_stop_409_raises(action: str, code: str) -> None:
    c, t = client(err(409, code))
    with pytest.raises(SquareCloudAPIError) as info:
        getattr(c.databases, action)(DB)
    assert (info.value.status, info.value.code, info.value.message) == (409, code, '')
    assert len(t.calls) == 1

    async def main() -> None:
        async with AsyncSquareCloud(
            KEY, transport=MockTransport([err(409, code)])
        ) as ac:
            await getattr(ac.databases, action)(DB)

    with pytest.raises(SquareCloudAPIError) as info:
        asyncio.run(main())
    assert (info.value.status, info.value.code) == (409, code)


def test_busy_gives_up_after_max_retries() -> None:
    c, t = client(*[err(503, 'UPLOAD_BUSY') for _ in range(3)])
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.commit(APP, b'PK')
    assert info.value.code == 'UPLOAD_BUSY'
    assert len(t.calls) == 3


# Request shape --------------------------------------------------------------


def test_headers_and_timeouts() -> None:
    ok = FakeResponse(200, {'status': 'success', 'response': {'id': APP}})
    c, t = client(ok, FakeResponse(200), timeout=7)
    c.apps.get(APP)
    c.apps.envs.set(APP, {'A': '1'})
    get, post = t.calls
    assert get.headers == {
        'Authorization': KEY,
        'User-Agent': f'squarecloud-sdk-py/{__version__}',
        'Accept': 'application/json',
    }
    assert post.headers['Content-Type'] == 'application/json'
    assert get.timeout == 7


def test_user_agent_override_replaces_the_header() -> None:
    c, t = client(FakeResponse(200), user_agent='my-bot/1.0')
    c.apps.start(APP)
    assert t.calls[0].headers['User-Agent'] == 'my-bot/1.0'


def test_url_escaping() -> None:
    path = '/a b&c=d#e+f%20g?h'
    c, t = client(
        FakeResponse(
            200,
            {'status': 'success', 'response': {'encoding': 'base64', 'data': 'aGk='}},
        )
    )
    assert c.apps.files.read('evil/../id', path) == b'hi'
    call = t.calls[0]
    assert '/apps/evil%2F..%2Fid/files/content?' in call.url
    assert call.query == {'path': [path], 'encoding': ['base64']}


def test_composite_workspace_id_is_kept() -> None:
    c, t = client(FakeResponse(200))
    c.apps.start(f'{APP}-{DB}')
    assert t.calls[0].path == f'/v2/apps/{APP}-{DB}/start'


def test_base_url_is_configurable() -> None:
    c, t = client(FakeResponse(200), base_url='http://localhost:8080/v2/')
    c.apps.stop(APP)
    assert t.calls[0].url == f'http://localhost:8080/v2/apps/{APP}/stop'


def test_absent_empty_and_false_query_values_are_omitted() -> None:
    c, t = client()
    t.handler = lambda _: FakeResponse(200, {'status': 'success', 'response': []})
    c.apps.files.list(APP)
    c.apps.files.list(APP, '')
    c.apps.status(APP)
    c.apps.status_all(workspace_id='')
    c.account.snapshots(scope=None)
    c.apps.network.errors(APP, 'a', 'b', include_4xx=False)
    assert all('?' not in x.url for x in t.calls[:-1])
    assert t.calls[-1].query == {'start': ['a'], 'end': ['b']}
    # User filters: False is dropped, True is 'true', 0 is kept.
    c._r('GET', '/x', query={'a': True, 'b': False, 'c': 0})
    assert t.calls[-1].query == {'a': ['true'], 'c': ['0']}


def test_files_write_encodings() -> None:
    c, t = client(*[FakeResponse(200)] * 5)
    c.apps.files.write(APP, '/a.txt', 'olá')
    c.apps.files.write(APP, 'b.txt', 'olá'.encode())
    c.apps.files.write(APP, '/c.bin', b'\xff\x00')
    c.apps.files.write(APP, '/empty', '')
    c.apps.files.write(APP, '/empty.bin', b'')
    b64 = {'encoding': 'base64'}
    assert [x.json() for x in t.calls] == [
        {'path': '/a.txt', 'content': 'olá'},  # a str is plain text
        {'path': 'b.txt', 'content': 'b2zDoQ==', **b64},  # path sent verbatim
        {'path': '/c.bin', 'content': '/wA=', **b64},
        {'path': '/empty', 'content': ''},  # an empty file is valid
        {'path': '/empty.bin', 'content': '', **b64},
    ]


ALL_BYTES = bytes(range(256))
TEXT = 'olá, 世界 🚀\n'


@pytest.mark.parametrize('data', [ALL_BYTES, TEXT.encode(), b''])
def test_files_round_trip_bytes_through_base64(data: bytes) -> None:
    encoded = base64.b64encode(data).decode()
    c, t = client(
        FakeResponse(200),
        FakeResponse(
            200,
            {'status': 'success', 'response': {'encoding': 'base64', 'data': encoded}},
        ),
    )
    c.apps.files.write(APP, '/f', data)
    assert t.calls[0].json() == {'path': '/f', 'content': encoded, 'encoding': 'base64'}
    assert c.apps.files.read(APP, '/f') == data
    assert t.calls[1].query == {'path': ['/f'], 'encoding': ['base64']}


def test_files_write_text_is_sent_as_utf8_text() -> None:
    c, t = client(FakeResponse(200))
    c.apps.files.write(APP, '/t.txt', TEXT)
    assert t.calls[0].json() == {'path': '/t.txt', 'content': TEXT}
    assert TEXT.strip().encode() in (t.calls[0].body or b'')  # raw UTF-8


@pytest.mark.parametrize(
    ('status', 'code'),
    [(404, 'FILE_NOT_FOUND'), (403, 'BLOCKED_PATH'), (400, 'INVALID_PATH')],
)
def test_files_list_errors(status: int, code: str) -> None:
    c, t = client(err(status, code))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.files.list(APP, '/missing')
    assert (info.value.status, info.value.code) == (status, code)
    assert len(t.calls) == 1


@pytest.mark.parametrize(
    ('status', 'code'), [(400, 'INVALID_ENCODING'), (413, 'FILE_TOO_LARGE')]
)
def test_files_read_errors(status: int, code: str) -> None:
    c, _ = client(err(status, code))
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.files.read(APP, '/big.bin')
    assert (info.value.status, info.value.code) == (status, code)


def test_deploy_error_event_carries_code_and_message() -> None:
    event = {
        'id': 'git-1',
        'state': 'error',
        'date': '2026-09-27T00:00:00.000Z',
        'source': 'git',
        'code': 'CLONE_FAILED',
        'message': 'npm install failed',
    }
    c, _ = client(FakeResponse(200, {'status': 'success', 'response': [[event]]}))
    [[got]] = c.apps.deploys.list(APP)
    assert got == event
    assert (got['state'], got.get('code'), got.get('message')) == (
        'error',
        'CLONE_FAILED',
        'npm install failed',
    )


def test_files_write_rejects_more_than_10mb_locally() -> None:
    c, t = client()
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.files.write(APP, '/big', b'x' * (10 * 1024 * 1024 + 1))
    assert (info.value.status, info.value.code) == (0, 'FILE_TOO_LARGE')
    assert info.value.path == f'/v2/apps/{APP}/files'
    assert t.calls == []


def test_database_update_sends_ram_and_omits_unset() -> None:
    c, t = client(FakeResponse(200), FakeResponse(200))
    c.databases.update(DB, ram=1024)
    c.databases.update(DB, name='db')
    assert [x.json() for x in t.calls] == [{'ram': 1024}, {'name': 'db'}]


def test_optional_fields_do_not_raise() -> None:
    c, _ = client(
        FakeResponse(200, {'status': 'success', 'response': {}}),
        FakeResponse(200, {'status': 'success'}),
        FakeResponse(
            200, {'status': 'success', 'response': {'id': DB, 'password': 'p'}}
        ),
    )
    assert c.apps.deploys.current(APP) == {}
    c2, _ = client(*[FakeResponse(200, {'status': 'success', 'response': {}})] * 3)
    net = c2.apps.network
    assert net.analytics(APP, '2026-01-01', '2026-01-02') is None
    assert net.errors(APP, '2026-01-01', '2026-01-02') is None
    assert net.performance(APP, '2026-01-01', '2026-01-02') is None
    assert c.databases.reset_credentials(DB, 'certificate') == ''
    created = c.databases.create('db', type='redis', version='7', memory=256)
    assert 'certificate' not in created


def test_null_string_results_are_empty() -> None:
    def null(key: str) -> FakeResponse:
        return FakeResponse(200, {'status': 'success', 'response': {key: None}})

    c, _ = client(null('logs'), null('webhook'), null('certificate'), null('code'))
    assert c.apps.logs(APP) == ''
    assert c.apps.deploys.set_webhook(APP, 'token') == ''
    assert c.databases.certificate(DB) == ''
    assert c.workspaces.members.invite_code() == ''


def test_link_github_app_without_repository_is_empty() -> None:
    c, _ = client(FakeResponse(200, {'status': 'fail'}))
    assert not c.apps.deploys.link_github_app(APP, 'o/r', 'main')


def test_unknown_fields_are_kept() -> None:
    user = {
        'id': '1',
        'name': 'n',
        'email': 'e',
        'locale': 'en',
        'plan': {},
        'created_at': 'x',
        'brand_new': 1,
    }
    c, _ = client(
        FakeResponse(
            200,
            {
                'status': 'success',
                'response': {'user': user, 'applications': [], 'databases': []},
            },
        )
    )
    assert c.account.me()['user']['brand_new'] == 1  # type: ignore[typeddict-item]


def test_status_all_keeps_stopped_apps() -> None:
    items = [
        {'id': 'a', 'running': True, 'cpu': '1%', 'ram': '1MB'},
        {'id': 'b', 'running': False},
    ]
    c, t = client(FakeResponse(200, {'status': 'success', 'response': items}))
    assert c.apps.status_all(workspace_id=DB) == items
    assert t.calls[0].query == {'workspaceId': [DB]}


def test_snapshot_items_pass_through_verbatim() -> None:
    items = [
        {
            'name': 'n1',
            'size': 1,
            'modified': 'x',
            'key': 'k?versionId=not-this-one',
            'version_id': '3/L4kqtJlc+rmSpX==',
            'url': 'https://s/n1.zip?sig=1',
        }
    ]
    c, t = client()
    t.handler = lambda _: FakeResponse(200, {'status': 'success', 'response': items})
    assert c.apps.snapshots.list(APP) == items  # nothing parsed out of `key`
    assert c.databases.snapshots.list(DB) == items
    assert c.account.snapshots() == items


def test_rejects_empty_api_key() -> None:
    with pytest.raises(ValueError):
        SquareCloud('  ')


def test_envs_delete_accepts_one_name() -> None:
    c, t = client(*[FakeResponse(200, {'status': 'success', 'response': {}})] * 2)
    c.apps.envs.delete(APP, 'API_KEY')
    c.apps.envs.delete(APP, ('A', 'B'))
    assert [x.json() for x in t.calls] == [{'envs': ['API_KEY']}, {'envs': ['A', 'B']}]


def test_ai_openai_error_without_code_uses_type() -> None:
    body = {'error': {'message': 'bad', 'type': 'invalid_request_error'}}
    c, _ = client(FakeResponse(400, body))
    with pytest.raises(SquareCloudAPIError) as info:
        c.ai.chat({'messages': [{'role': 'user', 'content': 'hi'}]})
    assert info.value.code == 'invalid_request_error'


def test_files_write_rejects_large_text_before_encoding() -> None:
    c, t = client()
    with pytest.raises(SquareCloudAPIError) as info:
        c.apps.files.write(APP, '/big', 'é' * (5 * 1024 * 1024 + 1))  # 10 MB + 2
    assert info.value.code == 'FILE_TOO_LARGE'
    assert t.calls == []


def test_datetimes_are_sent_as_utc_rfc3339() -> None:
    c, t = client(*[FakeResponse(200, {'status': 'success', 'response': []})] * 2)
    aware = datetime(2026, 9, 1, 3, tzinfo=timezone(timedelta(hours=3)))
    c.apps.network.logs(APP, aware, '2026-09-02T00:00:00Z')
    assert t.calls[0].query == {
        'start': ['2026-09-01T00:00:00Z'],
        'end': ['2026-09-02T00:00:00Z'],
    }
    naive = datetime(2026, 9, 1, 12)  # local time, as in the stdlib
    c.apps.network.logs(APP, naive, naive)
    sent = t.calls[1].query['start'][0]
    assert sent.endswith('Z')
    assert datetime.fromisoformat(sent) == naive.astimezone()


# Local file errors ----------------------------------------------------------


def test_async_calls_run_off_the_event_loop_thread() -> None:
    threads: list[int] = []

    def answer(call: Call) -> FakeResponse:
        threads.append(threading.get_ident())
        return FakeResponse(200, {'status': 'success', 'response': {'logs': 'ok'}})

    async def main() -> str:
        async with AsyncSquareCloud(KEY, transport=MockTransport(handler=answer)) as c:
            return await c.apps.logs(APP)

    assert asyncio.run(main()) == 'ok'
    assert threads and threads[0] != threading.get_ident()
