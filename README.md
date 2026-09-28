<div align="center">
  <img alt="Square Cloud Banner" src="https://cdn.squarecloud.app/png/github-readme.png">
</div>

<h1 align="center">squarecloud-api</h1>

<p align="center">The official Python SDK for the <a href="https://squarecloud.app" target="_blank">Square Cloud</a> API.</p>

<div align="center">
  <a href="https://pypi.org/project/squarecloud-api/"><img alt="PyPI Version" src="https://img.shields.io/pypi/v/squarecloud-api"></a>
  <img alt="License" src="https://img.shields.io/pypi/l/squarecloud-api">
  <img alt="Downloads" src="https://img.shields.io/pypi/dm/squarecloud-api">
</div>

- **Zero runtime dependencies**: only the standard library (`http.client`, `json`, `ssl`), with one keep-alive connection per thread.
- Runs on **Python 3.11+**, sync (`SquareCloud`) and async (`AsyncSquareCloud`), fully typed (`TypedDict` responses, `py.typed`).
- Covers all **67 operations** of the Square Cloud API, checked against the pinned OpenAPI spec on every CI run.
- Uploads and snapshot downloads **stream**; realtime logs and status come as an **iterator** (or `async for`).
- **One error type**, `SquareCloudAPIError`, for every API, network and local failure.

[Documentation](https://docs.squarecloud.app/en/sdks/py/client) · [Releases](https://github.com/squarecloudofc/sdk-api-py/releases) · [Migration guide](MIGRATION.md)

## Installation

```bash
pip install squarecloud-api
uv add squarecloud-api
poetry add squarecloud-api
```

Requires Python 3.11 or newer.

## API key

Create one at [squarecloud.app/account/security](https://squarecloud.app/account/security). A key can be limited to scopes (`apps:read`, `apps:deploy`, ...) and to specific apps or databases. A call outside those limits raises `SquareCloudAPIError` with 403 `MISSING_SCOPE` or `RESOURCE_NOT_ALLOWED`, and list endpoints return only the resources the key can see. An unknown, revoked or expired key is 401 `ACCESS_DENIED`.

## Quick start

```python
import os
from squarecloud import SquareCloud

with SquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client:
    me = client.account.me()
    print(me['user']['name'], [app['name'] for app in me['applications']])

    app_id = me['applications'][0]['id']
    client.apps.restart(app_id)
    print(client.apps.logs(app_id))
```

The same API with `await`:

```python
import asyncio
import os

from squarecloud import AsyncSquareCloud


async def main() -> None:
    async with AsyncSquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client:
        statuses = await client.apps.status_all()
        print([s['id'] for s in statuses if s['running']])


asyncio.run(main())
```

More in [`examples/`](examples): [apps](examples/apps.py), [realtime](examples/realtime.py), [snapshots](examples/snapshots.py), [databases](examples/databases.py), [workspaces](examples/workspaces.py), [async client](examples/async_client.py).

## Configuration

```python
import os

from squarecloud import BASE_URL, SquareCloud, __version__

client = SquareCloud(
    os.environ['SQUARECLOUD_API_KEY'],
    base_url=BASE_URL,  # the options are keyword-only; these are the defaults
    timeout=30.0,
    max_retries=2,
    transport=None,
    user_agent=f'squarecloud-sdk-py/{__version__}',
)
```

| Option | Default | Notes |
|---|---|---|
| `api_key` | required | Sent raw in `Authorization`. An empty or whitespace-only key raises `ValueError`. |
| `base_url` | `BASE_URL` = `https://api.squarecloud.app/v2` | A trailing `/` is stripped. |
| `timeout` | `30.0` | Seconds per socket operation. `<= 0` disables every timeout, floors included. See [Retries, timeouts and rate limits](#retries-timeouts-and-rate-limits). |
| `max_retries` | `2` | Negative counts as 0. |
| `transport` | `HTTPTransport(timeout)` | Plug your own HTTP client (see below). |
| `user_agent` | `squarecloud-sdk-py/<version>` | Replaces the whole `User-Agent` header. |

`AsyncSquareCloud` takes the same arguments. Both clients are thread-safe; call `close()` (or use `with` / `async with`) to close their connections. The version is `squarecloud.__version__`.

### Custom transport

`transport=` accepts any callable `transport(method, url, headers, body, timeout, stream)` that returns an object with `status`, `read()`, `readline()` and `close()` (an `http.client.HTTPResponse` qualifies). Use it for proxies, tracing or tests. `body` is `bytes`, an iterable of `bytes` chunks (with `Content-Length` already set) or `None`. `timeout` is the per-socket-operation timeout (raised for the held calls), or `None` for uploads, large file writes and the realtime stream, which a custom transport should bound on connect itself. The default `HTTPTransport(timeout)` still bounds their connect, and asks for gzip on every call except the streamed ones (realtime and snapshot downloads).

### Logging

The SDK logs each request at `DEBUG` on the `squarecloud` logger (method, path and status; never bodies or keys) and attaches only a `NullHandler`:

```python
import logging

logging.basicConfig()
logging.getLogger('squarecloud').setLevel(logging.DEBUG)
```

## API

Every app id may also be the composite `'<appId>-<workspaceId>'` to act on an app shared with you through a workspace. Optional modifiers are keyword-only.

| Group | Methods |
|---|---|
| `account` | `me()`, `snapshots(*, scope=None)` |
| `service` | `status()` (public route: the API does not check the key, but the client still needs a non-empty one) |
| `ai` | `chat(request)` (OpenAI-compatible, non-streaming) |
| `apps` | `create(file)`, `get(id)`, `delete(id)`, `status_all(*, workspace_id=None)`, `status(id, *, raw=False)`, `start(id)`, `stop(id)`, `restart(id)`, `logs(id)`, `metrics(id)`, `realtime(id)`, `domains()`, `load_balancers()`, `commit(id, file, *, path=None, filename=None)` |
| `apps.deploys` | `set_webhook(id, access_token)`, `link_github_app(id, repository, branch)`, `unlink_github_app(id)`, `list(id)`, `current(id)` |
| `apps.envs` | `get(id)`, `set(id, envs)`, `replace(id, envs)`, `delete(id, keys)` |
| `apps.files` | `list(id, path=None)`, `read(id, path)` → `bytes`, `write(id, path, content)`, `move(id, path, to)`, `delete(id, path)` |
| `apps.snapshots` | `list(id)`, `create(id)`, `restore(id, name, version_id)` |
| `apps.network` | `analytics(id, start, end, **filters)`, `errors(id, start, end, *, include_4xx=False)`, `logs(id, start, end)`, `performance(id, start, end)`, `dns(id)`, `set_domain(id, domain)`, `purge_cache(id)` |
| `databases` | `create(name, *, type, version, memory)`, `get(id)`, `update(id, *, name=None, ram=None)`, `delete(id)`, `start(id)`, `stop(id)`, `status(id, *, raw=False)`, `metrics(id)`, `status_all()`, `certificate(id)`, `reset_credentials(id, 'password' \| 'certificate')` → the new password, or `''` |
| `databases.snapshots` | `list(id)`, `create(id)`, `restore(id, name, version_id)` |
| `workspaces` | `create(name)`, `list()`, `get(id)`, `delete(id)`, `leave(id)` |
| `workspaces.members` | `add(workspace_id, code, group)`, `update(workspace_id, member_id, group)`, `remove(workspace_id, member_id)`, `invite_code()` |
| `workspaces.apps` | `add(workspace_id, app_id)`, `remove(workspace_id, app_id)` |
| client | `download_snapshot(url, dest)`, `close()` |

`AsyncSquareCloud` has the same groups and methods, each returning a coroutine (it runs the sync call in `asyncio.to_thread`), except `close()`, which is sync, and `apps.realtime(id)`, which returns an `AsyncRealtime` to use with `async for`. Field names are the API's own (`created_at`, `content_type`, `include_4xx`...), so the [API reference](https://docs.squarecloud.app/api-reference) applies as-is. Responses are `TypedDict`s from `squarecloud.types`: plain dicts, so fields the API adds later are kept. A string result is never `None` (`''` when the API sends nothing). `start`/`end` take an ISO 8601 string (sent as is) or a `datetime` (sent as UTC; a naive `datetime` is local time). The `analytics` filters are keyword-only: `country`, `ip`, `path`, `status`, `os`, `browser`, `protocol`, `referer`, `provider`, `content_type`, `bot`. `provider` takes the `'NAME (ASN)'` form the `providers` buckets report (`provider='GOOGLE (15169)'`); an invalid filter is 400 `INVALID_FILTER`. `metrics()` returns up to 24 h of 5-minute points, newest first. `status()` formats `cpu` and `ram` as strings (`'120.4MB'`); with `raw=True` they are numbers. Empty, `.` and `..` ids are rejected with `INVALID_ID` before sending, because they would reach another route. `apps.network.analytics`, `errors` and `performance` return `None` for a window with no traffic.

## Usage

### Uploads

`apps.create` and `apps.commit` take a path, `bytes` or a binary file object, and stream it: a path or a seekable file is never loaded into memory. A commit unpacks a `.zip` at `path` (the app root by default); any other file lands at `path/<filename>`. The filename is `filename=`, else the file's own name, else `app.zip` on create and `commit.zip` on commit. A zip over 100 MB fails locally with `FILE_TOO_LARGE` before anything is sent. Uploads have no timeout.

```python
created = client.apps.create('bot.zip')
client.apps.commit(created['id'], 'patch.zip', path='/src')
client.apps.commit(created['id'], b'print(1)', path='/src', filename='main.py')
```

### Files

```python
client.apps.files.write(app_id, '/config.json', '{"debug": false}')  # str or bytes
data: bytes = client.apps.files.read(app_id, '/config.json')
client.apps.files.move(app_id, '/config.json', '/config.old.json')
```

A `str` travels as text; `bytes` travel base64-encoded (binary-safe, about 1.33x on the wire). Empty content (`''` or `b''`) creates an empty file. Content over 10 MB fails locally with `FILE_TOO_LARGE`, and content over 1 MiB is sent without a timeout, like an upload; invalid content is 400 `INVALID_CONTENT`. `read` always asks for base64 and returns the decoded `bytes` (at most 10 MB, else 413 `FILE_TOO_LARGE`). `list` of a missing directory is 404 `FILE_NOT_FOUND`, and a blocked path is 403 `BLOCKED_PATH`. Paths are at most 256 characters.

### Snapshots

`create` returns `{'pending': True}` while the API is still generating the snapshot (HTTP 202 `SNAPSHOT_PROCESSING`). It then appears in `list` on its own, usually within 2 minutes: poll `list`, and never call `create` again, which is limited to one per 180 seconds and counts against the plan's daily snapshot quota.

```python
snapshot = client.apps.snapshots.create(app_id)
if not snapshot['pending']:
    client.download_snapshot(snapshot['url'], 'backups/')  # -> backups/<name>.zip

latest = max(client.apps.snapshots.list(app_id), key=lambda s: s['modified'])
client.apps.snapshots.restore(app_id, latest['name'], latest['version_id'])
client.download_snapshot(latest['url'], 'backups/')
```

Each listed item carries the API's `version_id` (what `restore` needs) and a signed download `url`, passed through as sent. `download_snapshot` never sends the API key to the snapshot host, streams to a `.part` file next to the target and renames it when complete, and bounds each read with `timeout`.

### Realtime

```python
with client.apps.realtime(app_id) as stream:
    for event in stream:
        if event['event'] == 'logs':
            print(event['stream'], event['line'])  # stdout | stderr
        elif event['event'] == 'status':
            print(event['status'].get('cpu'))  # always the full, merged state
        else:  # 'system' or 'error'
            print(event['data'])  # a code such as REALTIME_DISCONNECTED
```

Every event has `event`, `data` (the raw frame text) and `id`. The HTTP status is checked before streaming, so 429 `REALTIME_MAX_CONNECTIONS` raises. A dropped connection, or the API's `REALTIME_RECONNECT` hand-off, reopens up to 3 times in a row (a `logs` or `status` event resets the count), at most one open per 5.5 s to stay under the API's pace of one per 5 s; past that it raises `NETWORK_ERROR`. The open is timed until the response headers arrive; the stream itself is not. The loop ends on a clean close (10-minute server limit), on `REALTIME_DISCONNECTED`, or on `stream.close()` (safe from any thread, also mid-wait). With `AsyncSquareCloud`: `async with client.apps.realtime(app_id) as stream: async for event in stream: ...`. Max 5 concurrent streams per account and 30 per app.

### GitHub deploys

```python
# A GitHub webhook: returns its URL ('' when removed with '@')
url = client.apps.deploys.set_webhook(app_id, 'ghp_xxx')

# Or the Square Cloud GitHub App
repo = client.apps.deploys.link_github_app(app_id, 'octocat/hello-world', 'main')
print(repo['id'], repo['full_name'], repo['branch'])

current = client.apps.deploys.current(app_id)  # {} when nothing is set
client.apps.deploys.unlink_github_app(app_id)
```

Linking needs scope `apps:deploy` and a GitHub App installation on your account (403 `GITHUB_NOT_CONNECTED` otherwise). The repository must belong to a GitHub App installation your connected GitHub account holds (403 `REPOSITORY_NOT_AVAILABLE` otherwise), and that account needs write access to it (403 `REPOSITORY_PERMISSION_REQUIRED`). 502 `FAILED_TO_FETCH` means GitHub did not confirm the branch; it is safe to retry. A repository and branch can be linked to one app across all accounts (409 `REPOSITORY_BRANCH_ALREADY_CONFIGURED`; the other app's id appears only in `message`, and only when that app is yours). Re-linking needs an unlink first (400 `GIT_ALREADY_CONFIGURED`), and unlinking without a link is 400 `GIT_NOT_CONFIGURED`. Link and unlink share a limit of 3 calls per 60 s.

## Errors

Every API and network failure raises `SquareCloudAPIError` with `status`, `code`, `message`, `method`, `path` (`'/v2/apps/...'`, never the query string) and `cause`. Local file problems, such as a missing upload path or an unwritable download destination, raise `OSError`.

```python
from squarecloud import SquareCloudAPIError

try:
    client.apps.start(app_id)
except SquareCloudAPIError as e:
    print(e)  # POST /v2/apps/<id>/start: HTTP 404 APP_NOT_FOUND
    if e.code == 'MISSING_SCOPE':
        ...
```

- No response: `status` `0` with `code` `NETWORK_ERROR` (original exception in `cause`) or `TIMEOUT`.
- Local checks, nothing sent: `status` `0` with `FILE_TOO_LARGE`, or `INVALID_ID` for an id that is empty, `.` or `..`.
- `message` is the server's explanation, or `''` when it sent only a code. A body without a code (a proxy page, a failed snapshot download) is `UNKNOWN_ERROR`, with the server's message when it sent one and `HTTP <status>` otherwise; a 2xx body that is not JSON is `UNKNOWN_ERROR` with `Invalid JSON in HTTP <status> response`.
- Start, stop and restart refusals are 409 with only a code (`message` is `''`): `CONTAINER_ALREADY_STARTED`, `CONTAINER_ALREADY_STOPPED`, `CONTAINER_TEMPORARILY_SUSPENDED` (apps), `CONTAINER_NOT_FOUND`, `CONTAINER_INSUFFICIENT_DISK_SPACE`, `CONTAINER_NETWORK_CONFLICT` or `ACTION_FAILED`. They are errors: check `e.code` if an already started or stopped resource is fine for you. A 2xx reply whose body is `{"status": "error"}` also raises; a 202 `SNAPSHOT_PROCESSING` stays `{'pending': True}`.
- `ai.chat()` errors, auth, 429 and 503 included, carry the OpenAI error's lowercase `code` (`access_denied`, `upgrade_required`, `rate_limit_exceeded`, `server_overloaded`, `database_unavailable`, ...), or its `type` when there is no code.
- The `SquareCloudAPIError` docstring lists every known API code. The list grows: treat an unknown code as a generic failure of its HTTP status.
- `str(e)` is `<METHOD> <path>: HTTP <status> <CODE>: <message>`, without `HTTP <status>` when the status is `0` and without `: <message>` when it is empty.

## Retries, timeouts and rate limits

- **Timeouts:** `timeout` (30 s) applies per socket operation. Calls the server holds open wait at least 120 s (`start`/`stop`/`restart` of apps and databases, `databases.create`, snapshot `create`/`restore`), and so does `ai.chat()`, whose gateway has one 90 s deadline for the whole request and answers 503 `server_overloaded` past it; a larger `timeout` wins. `timeout <= 0` disables every timeout, floors included. Uploads and `files.write` above 1 MiB have no timeout; `realtime()` is timed only until it opens.
- **Retries:** the SDK retries only what is safe: network errors on `GET` (including a body cut off mid-read, realtime opens and `download_snapshot()` before the response), and 503 `UPLOAD_BUSY`/`ANALYTICS_BUSY` (plus `DATABASE_UNAVAILABLE` on `GET`), up to `max_retries` (2) times with exponential backoff (500 ms·2ⁿ, jitter, max 8 s). Timeouts, 429 and the AI's 503 `server_overloaded` (safe for you to retry) are never retried. `DATABASE_UNAVAILABLE` is not retried on other methods because it can fire after a mutation was applied; retrying an idempotent one (a `files.write`, an `envs.replace`, a `stop`) is up to you.
- **Rate limits:** every account has a global limit of requests per 60 s, set by its plan ([values](https://docs.squarecloud.app/en/api-reference/limitations-and-restrictions)). Going over it, or over a route's own limit, returns 429 `RATE_LIMITED` or `KEEP_CALM`. `RATE_LIMITED` can block the account, API key or IP for about 30 minutes; it is also the limit of the network endpoints and `account.snapshots()`. `RATE_LIMIT` and `RATE_LIMIT_EXCEEDED` are its deprecated names. The API sends no `Retry-After`, which is why the SDK never retries a 429.

## Development

```bash
uv sync
uv run ruff format --check && uv run ruff check && uv run mypy && uv run pytest   # offline
uv build
```

The offline suites (`tests/test_transport.py`, `tests/test_http.py`, `tests/test_streams.py`, `tests/test_conformance.py`) use a mock transport or a loopback server and never reach the API. The live suite runs all 67 operations against the real API:

```bash
SQUARECLOUD_API_KEY=... uv run pytest -m live -s
```

> **Warning:** the live suite creates and deletes real resources (an app, a database and a workspace named `sdk-live-py-<timestamp>`) on the key's account. It is skipped without `SQUARECLOUD_API_KEY` and never runs in CI. Requests are spaced 2.1 s apart; run the JS, Python and Go live suites one after another, never at the same time.

## Contributing

Issues and pull requests are welcome at [squarecloudofc/sdk-api-py](https://github.com/squarecloudofc/sdk-api-py).

## License

MIT, see [LICENSE](LICENSE).

## Authors

Maintained by [Square Cloud](https://squarecloud.app).

Contributors:

- Robert Nogueira ([@robert-nogueira](https://github.com/robert-nogueira))
- Jhonatan Jeferson ([@Jhonatan-Jeferson](https://github.com/Jhonatan-Jeferson))
