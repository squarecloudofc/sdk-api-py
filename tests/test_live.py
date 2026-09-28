"""Live suite (SDK-STANDARD 10.1): all 67 operations against the real API.

    SQUARECLOUD_API_KEY=... uv run pytest -m live -s

It CREATES AND DELETES real resources (an app, a workspace and a database)
named ``sdk-live-py-<base36 ms>``. It is skipped without the key and never
runs in CI. Nothing it prints contains the key, a password or a certificate.
Run the JS, PY and GO suites one after another: they share the account's
per-user rate limits (github-app 3/60 s, domains 10/5 min) and snapshot
quota. Nothing external is configured: the custom domain is malformed (or
``'@'``), the webhook token is fake, and the GitHub link targets a
repository nobody installed.

Every successful result is checked against the method's return annotation
(``shape``), so a response the SDK types do not describe fails the run. At
the end it prints the HTTP statuses each spec operation answered and lists
the account again: anything left with the prefix is deleted and fails the
run.
"""

from __future__ import annotations

import io
import os
import random
import re
import threading
import time
import types
import typing
import zipfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal, ParamSpec, TypeVar, get_args, get_origin
from urllib.parse import urlsplit

import pytest
from test_conformance import CASES, GROUPS, template_of
from test_conformance import OPS as SPEC_OPS

from squarecloud import BASE_URL, HTTPTransport, SquareCloud, SquareCloudAPIError
from squarecloud.client import Body, Response
from squarecloud.types import RealtimeEvent, Snapshot, SnapshotCreated

pytestmark = pytest.mark.live

KEY = os.environ.get('SQUARECLOUD_API_KEY', '')
if not KEY.strip():
    pytest.skip('SQUARECLOUD_API_KEY is not set', allow_module_level=True)

PREFIX = 'sdk-live-py-'


def base36(n: int) -> str:
    digits = ''
    while n:
        n, r = divmod(n, 36)
        digits = '0123456789abcdefghijklmnopqrstuvwxyz'[r] + digits
    return digits or '0'


NAME = PREFIX + base36(time.time_ns() // 1_000_000)
MISSING = '0' * 32  # the id of a resource that does not exist
# Documented outcomes of plan-gated calls: reported as a skip, not a failure.
GATED = {
    'UPGRADE_REQUIRED',
    'upgrade_required',  # the AI route's OpenAI dialect (lowercase codes)
    'missing_scope',
    'INSUFFICIENT_MEMORY',
    'MISSING_SCOPE',
    'DAILY_SNAPSHOTS_LIMIT_REACHED',
    'WORKSPACE_LIMIT_REACHED',
}
# What the edge analytics routes answer for an app without a domain (500).
NO_DOMAIN = {
    'UNABLE_TO_FETCH_ANALYTICS',
    'UNABLE_TO_FETCH_ERRORS',
    'UNABLE_TO_FETCH_PERFORMANCE',
}
# Seconds between requests, the same in the JS, PY and GO suites. An API key
# gets 30 calls per 60 s on the smallest paid plan (plans.js), and going past
# it blocks the key for 30 minutes.
PACE = 2.1
KEEP_CALM_RETRIES = 7  # 70 s: outlasts the per-user 60 s windows another
# SDK's live suite may have just used with the same key (github-app,
# purge_cache, snapshot restore).

P = ParamSpec('P')
R = TypeVar('R')

# (method, spec path) -> the HTTP statuses it answered (0: no response).
statuses: dict[tuple[str, str], set[int]] = {}
counting = True  # off during the sweep and the final listing


class PacedTransport(HTTPTransport):
    """The default transport, one request per ``PACE`` seconds: API calls,
    retries, realtime opens and snapshot downloads alike. Records the status
    of every API request per spec operation."""

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._next = 0.0

    def __call__(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        body: Body,
        timeout: float | None,
        stream: bool,
    ) -> Response:
        with self._lock:
            now = time.monotonic()
            wait = self._next - now
            self._next = max(now, self._next) + PACE
        if wait > 0:
            time.sleep(wait)
        seen = None
        if counting and url.startswith(BASE_URL):
            key = (method, template_of(method, urlsplit(url).path))
            seen = statuses.setdefault(key, set())
        try:
            resp = super().__call__(method, url, headers, body, timeout, stream)
        except BaseException:
            if seen is not None:
                seen.add(0)
            raise
        if seen is not None:
            seen.add(resp.status)
        return resp


@pytest.fixture(autouse=True)
def sleeps() -> None:
    """Overrides the offline suites' instant backoff: the real API needs the
    real waits (retry backoff, the 5.5 s realtime reopen pace)."""


# Operation names ('apps.envs.delete') by (id of the group, method name), and
# the ones this run has touched, by success or by an asserted error.
OPS: dict[tuple[int, str], str] = {}
touched: set[str] = set()
errors_seen: dict[str, set[str]] = {}  # op -> {'404 APP_NOT_FOUND', ...}
mismatches: set[str] = set()  # results the SDK types do not describe
undeclared: set[str] = set()  # keys the API sends that the types omit


def index(group: Any, prefix: str) -> None:
    for name in dir(group):
        if not name.startswith('_'):
            value = getattr(group, name)
            if callable(value):
                OPS[(id(group), name)] = prefix + name
            else:
                index(value, f'{prefix}{name}.')


def op_of(fn: Callable[..., object]) -> str:
    return OPS.get((id(getattr(fn, '__self__', None)), getattr(fn, '__name__', '')), '')


def shape(value: Any, tp: Any, where: str) -> list[str]:
    """Where ``value`` does not fit the SDK type ``tp``. Type names only,
    never values (a result may hold a password). A key the type does not
    declare comes back prefixed with ``+``."""
    origin, args = get_origin(tp), get_args(tp)
    got = type(value).__name__
    if tp is Any:
        return []
    if tp is None or tp is type(None):
        return [] if value is None else [f'{where}: {got}, expected None']
    if origin in (typing.Union, types.UnionType):
        options = [shape(value, option, where) for option in args]
        best = min(options, key=lambda o: sum(not e.startswith('+') for e in o))
        if all(e.startswith('+') for e in best):
            return best
        return [f'{where}: {got} fits none of {tp}']
    if origin is Literal:
        return [] if value in args else [f'{where}: {value!r:.40} not in {args}']
    if origin is list:
        if not isinstance(value, list):
            return [f'{where}: {got}, expected list']
        return sorted({e for v in value for e in shape(v, args[0], f'{where}[]')})
    if origin is dict:
        if not isinstance(value, dict):
            return [f'{where}: {got}, expected dict']
        return sorted({e for v in value.values() for e in shape(v, args[1], where)})
    if typing.is_typeddict(tp):
        if not isinstance(value, dict):
            return [f'{where}: {got}, expected {tp.__name__}']
        hints = typing.get_type_hints(tp)
        out = [
            f'{where}.{k}: missing' for k in sorted(tp.__required_keys__ - value.keys())
        ]
        out += [f'+{where}.{k}' for k in sorted(value.keys() - hints.keys())]
        for k in sorted(value.keys() & hints.keys()):
            out += shape(value[k], hints[k], f'{where}.{k}')
        return out
    if tp is float:
        ok = isinstance(value, int | float) and not isinstance(value, bool)
    elif tp is int:
        ok = isinstance(value, int) and not isinstance(value, bool)
    else:
        ok = isinstance(value, tp)
    return [] if ok else [f'{where}: {got}, expected {getattr(tp, "__name__", tp)}']


def check(where: str, value: Any, tp: Any) -> None:
    for e in shape(value, tp, where):
        (undeclared if e.startswith('+') else mismatches).add(e.lstrip('+'))


def call(fn: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
    """Retries 429 ``KEEP_CALM`` every 10 s, at most ``KEEP_CALM_RETRIES``
    times. Test-only: the SDK never retries a 429. Checks the result against
    the method's return annotation."""
    op = op_of(fn)
    if op and counting:
        touched.add(op)
    for attempt in range(KEEP_CALM_RETRIES + 1):
        try:
            result = fn(*args, **kwargs)
        except SquareCloudAPIError as e:
            if op and counting:
                errors_seen.setdefault(op, set()).add(f'{e.status} {e.code}')
            if (e.status, e.code) != (429, 'KEEP_CALM') or attempt == KEEP_CALM_RETRIES:
                raise
            time.sleep(10)
            continue
        if op:
            check(op, result, typing.get_type_hints(fn)['return'])
        return result
    raise AssertionError('unreachable')


def fails(
    fn: Callable[P, object], *args: P.args, **kwargs: P.kwargs
) -> SquareCloudAPIError:
    with pytest.raises(SquareCloudAPIError) as info:
        call(fn, *args, **kwargs)
    return info.value


def is_4xx(e: SquareCloudAPIError) -> bool:
    return 400 <= e.status < 500 and e.status != 429


def fails_4xx(
    fn: Callable[P, object], *args: P.args, **kwargs: P.kwargs
) -> SquareCloudAPIError:
    e = fails(fn, *args, **kwargs)
    assert is_4xx(e), (e.status, e.code)
    return e


def tolerate(
    codes: set[str], op: str, fn: Callable[P, R], *args: P.args, **kwargs: P.kwargs
) -> R | None:
    """Success, or one of ``codes``, reported as ``skip <op>: <code>``."""
    try:
        return call(fn, *args, **kwargs)
    except SquareCloudAPIError as e:
        if e.code not in codes:
            raise
        print(f'skip {op}: {e.code}')
        return None


def remove(fn: Callable[[str], None], resource_id: str) -> None:
    """A cleanup delete: a 404 (already gone) is fine. A delete within 120 s
    of a restore gets 403 ``RESTORE_IN_PROGRESS``: retried every 10 s."""
    deadline = time.monotonic() + 130
    while True:
        try:
            call(fn, resource_id)
            return
        except SquareCloudAPIError as e:
            if e.status == 404:
                return
            if e.code != 'RESTORE_IN_PROGRESS' or time.monotonic() > deadline:
                raise
            time.sleep(10)


def make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buf.getvalue()


def app_zip(web: bool) -> bytes:
    config = [
        f'DISPLAY_NAME={NAME}',
        'MAIN=index.js',
        f'MEMORY={512 if web else 256}',
        'VERSION=recommended',
    ]
    if web:
        config.append(f'SUBDOMAIN={NAME}')
        code = (
            "require('node:http').createServer((_, res) => res.end('ok'))"
            ".listen(process.env.PORT || 80, () => console.log('listening'));\n"
        )
    else:
        code = "setInterval(() => console.log('tick'), 1000);\n"
    # package.json is required for Node (400 INVALID_DEPENDENCY without it)
    return make_zip(
        {
            'squarecloud.app': '\n'.join(config) + '\n',
            'package.json': '{}\n',
            'index.js': code,
        }
    )


def verify_download(client: SquareCloud, url: str, dest: Path) -> None:
    """Downloads a whole snapshot and checks the zip magic."""
    data = Path(call(client.download_snapshot, url, dest)).read_bytes()
    assert data[:4] == b'PK\x03\x04', 'zip header'
    assert len(data) > 22, 'zip size'
    print(f'snapshot download: {len(data)} bytes, zip header ok')


def listed(
    created: SnapshotCreated | None, list_: Callable[[str], list[Snapshot]], id_: str
) -> Snapshot | None:
    """The newest listed snapshot. A pending one shows up within about 2
    minutes, so an empty list is polled every 10 s for up to 3 minutes."""
    if created and created['pending']:
        print('snapshot pending (202): polling the list')
    items = call(list_, id_)
    for _ in range(18):
        if items or not created:
            break
        time.sleep(10)
        items = call(list_, id_)
    if created:
        assert items, 'no snapshot listed'
    for s in items:
        assert s['version_id'], 'version_id sent by the API'
        assert s['url'].startswith('https://'), 'signed download url'
    return max(items, key=lambda s: s['modified']) if items else None


@dataclass
class LiveApp:
    id: str
    web: bool  # it got a domain: step 4 runs the website variant


@pytest.fixture(scope='module')
def client() -> Iterator[SquareCloud]:
    with SquareCloud(KEY, transport=PacedTransport()) as c:
        for group in GROUPS:
            index(getattr(c, group), f'{group}.')
        sweep(c)
        try:
            yield c
        finally:
            report()
            left_clean(c)


def owned(c: SquareCloud) -> list[tuple[Callable[[str], None], str, str]]:
    """(delete, id, name) of every resource with our prefix: only workspaces
    this account owns."""
    me = call(c.account.me)
    workspaces = [w for w in call(c.workspaces.list) if w['owner'] == me['user']['id']]
    return [
        (group.delete, item['id'], item['name'])
        for group, items in (
            (c.apps, me['applications']),
            (c.databases, me['databases']),
            (c.workspaces, workspaces),
        )
        for item in items
        if item['name'].startswith(PREFIX)
    ]


def sweep(c: SquareCloud) -> None:
    """Deletes what earlier runs left behind."""
    global counting
    counting = False
    try:
        for delete, id_, name in owned(c):
            try:
                remove(delete, id_)
            except SquareCloudAPIError as e:
                print(f'sweep {name}: {e.code}')
    finally:
        counting = True


def left_clean(c: SquareCloud) -> None:
    """The account is listed again: anything left is deleted and fails."""
    global counting
    counting = False
    left = owned(c)
    for delete, id_, _ in left:
        remove(delete, id_)
    assert not [name for _, _, name in left], 'resources were left behind'
    print('account is left clean')


def report() -> None:
    for method, path in sorted(SPEC_OPS, key=lambda o: (o[1], o[0])):
        seen = ' '.join(map(str, sorted(statuses.get((method, path), ())))) or '-'
        print(f'op {method} {path}: {seen}')
    for op, codes in sorted(errors_seen.items()):
        print(f'error {op}: {", ".join(sorted(codes))}')
    for key in sorted(undeclared):
        print(f'undeclared {key}')
    for key in sorted(mismatches):
        print(f'MISMATCH {key}')


@pytest.fixture(scope='module')
def app(client: SquareCloud) -> Iterator[LiveApp]:
    me = call(client.account.me)
    web = me['user']['plan']['memory']['available'] >= 512
    created = call(client.apps.create, app_zip(web))
    touched.add('apps.delete')  # the teardown deletes it
    try:
        assert re.fullmatch(r'[0-9a-f]{32}', created['id'])
        got = call(client.apps.get, created['id'])
        assert got['name'] == NAME
        # `domain` is the full host of a website, left out otherwise
        assert created.get('domain') == got.get('domain')
        assert created.get('cluster') == got['cluster']
        yield LiveApp(created['id'], bool(got.get('domain')))
    finally:
        remove(client.apps.delete, created['id'])


# 1. Read-only ------------------------------------------------------------------


def test_1_read_only(client: SquareCloud) -> None:
    assert isinstance(call(client.service.status)['status'], str)
    assert call(client.account.me)['user']['id']
    snapshots = tolerate(GATED, 'account.snapshots', client.account.snapshots)
    assert snapshots is None or isinstance(snapshots, list)
    assert isinstance(call(client.apps.status_all), list)
    assert isinstance(call(client.apps.domains), list)
    assert isinstance(call(client.apps.load_balancers)['limit'], int)
    assert isinstance(call(client.databases.status_all), list)
    assert isinstance(call(client.workspaces.list), list)
    # One invite code per 5 min per user: a recent run leaves it KEEP_CALM,
    # which outlasts the retries, so it is called once.
    invite_code = client.workspaces.members.invite_code
    touched.add('workspaces.members.invite_code')
    try:
        assert isinstance(invite_code(), str)
    except SquareCloudAPIError as e:
        if e.code != 'KEEP_CALM':
            raise
        print(f'skip workspaces.members.invite_code: {e.code}')


# 2. Error paths ------------------------------------------------------------------


def test_2_error_paths(client: SquareCloud) -> None:
    e = fails(client.apps.get, '..')
    assert (e.status, e.code) == (0, 'INVALID_ID')
    e = fails(client.apps.get, MISSING)
    assert (e.status, e.code) == (404, 'APP_NOT_FOUND')


# 3. App --------------------------------------------------------------------------


def watch_restart(client: SquareCloud, app_id: str) -> list[str]:
    """Realtime across a restart: the restart runs 3 s after the open, and a
    ``logs``/``status`` event must follow it. The cluster relays ``system
    REALTIME_DISCONNECTED`` when the container goes down, which ends the
    stream (SDK-STANDARD 6), so a stream that ended is reopened once."""
    seen: list[str] = []
    restarted = threading.Event()
    failure: list[BaseException] = []

    def restart() -> None:
        try:
            time.sleep(3)
            call(client.apps.restart, app_id)
            restarted.set()
        except BaseException as exc:
            failure.append(exc)

    def watch(seconds: float) -> bool:
        with call(client.apps.realtime, app_id) as stream:
            timer = threading.Timer(seconds, stream.close)
            timer.start()
            try:
                for event in stream:
                    check('apps.realtime', event, RealtimeEvent)
                    kind = event['event']
                    name = (
                        kind
                        if kind in ('logs', 'status')
                        else f'{kind}:{event["data"].split(" |")[0][:40]}'
                    )
                    if not seen or seen[-1] != name:
                        seen.append(name)
                    if restarted.is_set() and kind in ('logs', 'status'):
                        return True
            finally:
                timer.cancel()
        return False

    opened = time.monotonic()
    worker = threading.Thread(target=restart)
    worker.start()
    try:
        after = watch(120)
    finally:
        worker.join()
    if failure:
        raise failure[0]
    if not after:
        seen.append('(reopened)')
        time.sleep(max(0.0, 5.5 - (time.monotonic() - opened)))  # 1 open / 5 s
        after = watch(60)
    assert after, f'no logs/status event after the restart: {seen}'
    return seen


def test_3_app(client: SquareCloud, app: LiveApp) -> None:
    apps, app_id = client.apps, app.id
    summary = next(
        a for a in call(client.account.me)['applications'] if a['id'] == app_id
    )
    assert summary['name'] == NAME
    if app.web:
        domain = next(d for d in call(apps.domains) if d['app_id'] == app_id)
        assert domain['type'] == 'subdomain'
        assert domain['hostname'] == call(apps.get, app_id).get('domain')
    assert isinstance(call(apps.status, app_id)['running'], bool)
    assert isinstance(call(apps.status, app_id, raw=True)['cpu'], int | float)
    logs = tolerate({'LOGS_UNAVAILABLE'}, 'apps.logs', apps.logs, app_id)
    assert logs is None or isinstance(logs, str)
    assert isinstance(call(apps.metrics, app_id), list)
    call(apps.stop, app_id)
    call(apps.start, app_id)
    print('realtime:', ' > '.join(watch_restart(client, app_id)))

    envs = apps.envs
    assert call(envs.set, app_id, {'SDK_LIVE': '1'})['SDK_LIVE'] == '1'
    assert call(envs.get, app_id)['SDK_LIVE'] == '1'
    both = {'SDK_LIVE': '2', 'OTHER': 'x'}
    assert call(envs.replace, app_id, both) == both
    assert call(envs.delete, app_id, ['OTHER']) == {'SDK_LIVE': '2'}

    # UTF-8 text, binary (every byte value 0-255, then random bytes) and
    # empty files (str and bytes), each read back byte-exact over base64
    files = apps.files
    binary = bytes(range(256)) + random.randbytes(64 * 1024 - 256)
    text = 'héllo 🌍\n'
    written: list[tuple[str, str | bytes, bytes]] = [
        ('/sdk-live.txt', text, text.encode()),
        ('/sdk-live-utf8.txt', text.encode(), text.encode()),
        ('/sdk-live-bytes.bin', bytes(range(256)), bytes(range(256))),
        ('/sdk-live.bin', binary, binary),
        ('/sdk-live-empty.txt', '', b''),
        ('/sdk-live-empty.bin', b'', b''),
    ]
    for path, content, _ in written:
        call(files.write, app_id, path, content)
    for path, _, data in written:
        assert call(files.read, app_id, path) == data, path
    listing = call(files.list, app_id, '/')
    entry = next(f for f in listing if f['name'] == 'sdk-live.txt')
    assert entry['type'] == 'file'
    assert isinstance(entry['size'], int)
    assert isinstance(entry['lastModified'], int | float)  # mtimeMs
    bare = [f'{f["type"]} {f["name"]}' for f in listing if 'size' not in f]
    print(f'apps.files.list: {len(listing)} entries, without size: {bare}')
    assert isinstance(call(files.list, app_id), list)
    e = fails(files.list, app_id, '/sdk-live-missing-dir')
    assert (e.status, e.code) == (404, 'FILE_NOT_FOUND')
    call(files.move, app_id, '/sdk-live.txt', '/sdk-live-moved.txt')
    assert call(files.read, app_id, '/sdk-live-moved.txt') == text.encode()
    for path, _, _ in written[1:]:
        call(files.delete, app_id, path)
    call(files.delete, app_id, '/sdk-live-moved.txt')
    left = call(files.list, app_id, '/')
    assert not [f for f in left if f['name'].startswith('sdk-live')]

    # Commit without path (a plain file lands at the root under `filename`),
    # then with one (a zip is unpacked there). 1 commit per 5 s per app.
    call(apps.commit, app_id, b'// commit\n', filename='sdk-live-commit.js')
    time.sleep(5.5)
    zipped = make_zip({'inner.txt': 'zipped'})
    call(apps.commit, app_id, zipped, path='sdk-live-dir')
    root = {f['name'] for f in call(files.list, app_id, '/')}
    assert 'sdk-live-commit.js' in root
    assert call(files.read, app_id, '/sdk-live-dir/inner.txt') == b'zipped'

    deploys = apps.deploys
    assert all(isinstance(d, list) for d in call(deploys.list, app_id))
    assert isinstance(call(deploys.current, app_id), dict)
    e = fails_4xx(deploys.set_webhook, app_id, 'invalid')
    assert e.code == 'INVALID_ACCESS_TOKEN'
    # A well-formed fake token: stored on this app only, nothing is configured
    # on GitHub. Then removed with '@'.
    webhook = call(deploys.set_webhook, app_id, 'ghp_' + '0' * 36)
    assert re.fullmatch(r'https://\S+/git/webhook/\S+', webhook), 'webhook url'
    assert call(deploys.current, app_id).get('webhook') == webhook
    assert call(deploys.set_webhook, app_id, '@') == ''
    assert 'webhook' not in call(deploys.current, app_id)
    # The test account has no GitHub App installation
    e = fails(deploys.link_github_app, app_id, 'squarecloudofc/does-not-exist', 'main')
    assert (e.status, e.code) == (403, 'GITHUB_NOT_CONNECTED')
    e = fails(deploys.unlink_github_app, app_id)
    assert (e.status, e.code) == (400, 'GIT_NOT_CONFIGURED')


# 4. Network ----------------------------------------------------------------------


def test_4_network(client: SquareCloud, app: LiveApp) -> None:
    net = client.apps.network
    end = datetime.now(UTC)
    start = end - timedelta(hours=24)
    window: list[tuple[str, Callable[..., object], dict[str, Any]]] = [
        ('analytics', net.analytics, {}),
        ('errors', net.errors, {'include_4xx': True}),
        # Pro and Enterprise only: 403 UPGRADE_REQUIRED on the other plans
        ('logs', net.logs, {}),
        ('performance', net.performance, {}),
    ]
    for op, fn, kwargs in window:
        if not app.web:
            # No domain: the plan gate's 4xx, or the edge query's 500.
            e = fails(fn, app.id, start, end, **kwargs)
            assert is_4xx(e) or (e.status == 500 and e.code in NO_DOMAIN), (
                op,
                e.status,
                e.code,
            )
        elif op in ('logs', 'performance'):
            tolerate(GATED, f'apps.network.{op}', fn, app.id, start, end, **kwargs)
        else:
            call(fn, app.id, start, end, **kwargs)
    if app.web:
        tolerate({'NO_CUSTOM_DOMAIN'}, 'apps.network.dns', net.dns, app.id)
    else:
        fails_4xx(net.dns, app.id)
    # The edge purge can fail upstream: the call itself is what is checked.
    tolerate(
        {'PURGE_CACHE_FAILED'}, 'apps.network.purge_cache', net.purge_cache, app.id
    )
    # Never a well-formed domain: on a paid plan it is registered at the edge.
    # A malformed one is rejected first on every plan, and '@' on an app
    # without a custom domain only clears the field.
    e = fails_4xx(net.set_domain, app.id, 'not a domain')
    assert e.code == 'INVALID_DOMAIN'
    tolerate(GATED, 'apps.network.set_domain', net.set_domain, app.id, '@')


# 5. Snapshots --------------------------------------------------------------------


def test_5_snapshots(client: SquareCloud, app: LiveApp, tmp_path: Path) -> None:
    snapshots = client.apps.snapshots
    created = tolerate(GATED, 'apps.snapshots.create', snapshots.create, app.id)
    if created and not created['pending']:
        verify_download(client, created['url'], tmp_path)
    latest = listed(created, snapshots.list, app.id)
    if latest:
        every = tolerate(
            GATED, 'account.snapshots', client.account.snapshots, scope='applications'
        )
        if every is not None:
            ids = {s['version_id'] for s in every}
            assert latest['version_id'] in ids, 'account.snapshots lists it'
        call(snapshots.restore, app.id, latest['name'], latest['version_id'])
    else:
        fails_4xx(snapshots.restore, app.id, 'sdk-live-missing', '0')


# 6. Workspace --------------------------------------------------------------------


def test_6_workspace(client: SquareCloud, app: LiveApp) -> None:
    """Without the plan for workspaces, every call runs against a missing one
    and must fail with a 4xx."""
    ws = client.workspaces
    created = tolerate(GATED, 'workspaces.create', ws.create, NAME)
    ws_id = created['id'] if created else MISSING
    try:
        if created:
            assert created['name'] == NAME
            assert call(ws.get, ws_id)['name'] == NAME
            call(ws.apps.add, ws_id, app.id)
            got = call(ws.get, ws_id)
            assert app.id in {a['id'] for a in got['applications']}
            assert 'owner' in {m['group'] for m in got['members']}
            # The composite `<appId>-<workspaceId>` reaches the shared app
            assert call(client.apps.get, f'{app.id}-{ws_id}')['id'] == app.id
            listed_ids = {
                s['id'] for s in call(client.apps.status_all, workspace_id=ws_id)
            }
            assert app.id in listed_ids
            call(ws.apps.remove, ws_id, app.id)
        else:
            fails_4xx(ws.get, ws_id)
            fails_4xx(ws.apps.add, ws_id, app.id)
            fails_4xx(ws.apps.remove, ws_id, app.id)
        fails_4xx(ws.members.add, ws_id, 'invalid', 'view')
        for e in (
            fails_4xx(ws.members.update, ws_id, '0', 'view'),
            fails_4xx(ws.members.remove, ws_id, '0'),
        ):
            if created:  # an unknown member of an existing workspace
                assert (e.status, e.code) == (404, 'MEMBER_NOT_FOUND')
        fails_4xx(ws.leave, ws_id)  # the owner cannot leave
    finally:
        if created:
            remove(ws.delete, ws_id)
    if created is None:
        fails_4xx(ws.delete, ws_id)
    # Minutes after the create, the first 5-min metric points may exist
    points = call(client.apps.metrics, app.id)
    print(f'apps.metrics: {len(points)} points')


# 7. Database ---------------------------------------------------------------------


def test_7_database(client: SquareCloud, tmp_path: Path) -> None:
    """Without the plan for databases, every call runs against a missing one
    and must fail with a 4xx."""
    dbs = client.databases
    created = tolerate(
        GATED,
        'databases.create',
        dbs.create,
        NAME,
        type='redis',  # the smallest engine: 512 MB
        version='8',
        memory=512,
    )
    if created is None:
        for fn in (
            dbs.get,
            dbs.status,
            dbs.metrics,
            dbs.certificate,
            dbs.stop,
            dbs.start,
            dbs.snapshots.create,
            dbs.snapshots.list,
            dbs.delete,
        ):
            fails_4xx(fn, MISSING)
        fails_4xx(dbs.status, MISSING, raw=True)
        fails_4xx(dbs.update, MISSING, name=NAME)
        fails_4xx(dbs.reset_credentials, MISSING, 'password')
        fails_4xx(dbs.snapshots.restore, MISSING, 'sdk-live-missing', '0')
        return
    db_id, has_password = created['id'], bool(created.get('password'))
    del created  # holds the password: never in an assertion message
    try:
        assert has_password, 'a password is returned once'
        assert call(dbs.get, db_id)['name'] == NAME
        assert isinstance(call(dbs.status, db_id)['running'], bool)
        assert isinstance(call(dbs.status, db_id, raw=True)['cpu'], int | float)
        assert isinstance(call(dbs.metrics, db_id), list)
        call(dbs.update, db_id, name=NAME + '-2')
        assert call(dbs.get, db_id)['name'] == NAME + '-2'
        assert call(dbs.certificate, db_id) != '', 'certificate'
        assert call(dbs.reset_credentials, db_id, 'password') != '', 'new password'
        time.sleep(3.1)  # 1 reset per 3 s per user
        assert call(dbs.reset_credentials, db_id, 'certificate') == ''
        assert db_id in {s['id'] for s in call(dbs.status_all)}
        call(dbs.stop, db_id)
        call(dbs.start, db_id)
        try:
            call(dbs.start, db_id)
            print('databases.start again: success')
        except SquareCloudAPIError as e:
            assert (e.status, e.code) in {
                (409, 'CONTAINER_ALREADY_STARTED'),
                (409, 'ACTION_FAILED'),
            }, (e.status, e.code)
            print(f'databases.start again: 409 {e.code}')
        snapshot = tolerate(
            GATED, 'databases.snapshots.create', dbs.snapshots.create, db_id
        )
        if snapshot and not snapshot['pending']:
            verify_download(client, snapshot['url'], tmp_path)
        latest = listed(snapshot, dbs.snapshots.list, db_id)
        if latest:
            call(dbs.snapshots.restore, db_id, latest['name'], latest['version_id'])
        else:
            fails_4xx(dbs.snapshots.restore, db_id, 'sdk-live-missing', '0')
    finally:
        # Right after a restore: remove() waits out RESTORE_IN_PROGRESS
        remove(dbs.delete, db_id)


# 8. AI ---------------------------------------------------------------------------


def test_8_ai(client: SquareCloud) -> None:
    reply = tolerate(
        GATED,
        'ai.chat',
        client.ai.chat,
        {'messages': [{'role': 'user', 'content': 'ping'}], 'max_tokens': 5},
    )
    if reply is not None:
        assert reply['choices']
        assert isinstance(reply['model'], str)
        assert isinstance(reply['usage']['total_tokens'], int)


# Coverage ------------------------------------------------------------------------


def test_9_every_operation_was_touched(app: LiveApp) -> None:
    """Runs only when the app exists: without it, steps 3 to 5 never ran.
    Every result also fit the SDK types."""
    assert {name for name, _, _ in CASES} - touched == set()
    assert not mismatches, sorted(mismatches)
