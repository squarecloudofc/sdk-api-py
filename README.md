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

- **Zero runtime dependencies**, and one reused connection per thread.
- Runs on **Python 3.11+**, with a sync `SquareCloud` client, an async `AsyncSquareCloud` client and typed responses.
- Covers all **69 operations** of the Square Cloud API, checked against the pinned OpenAPI spec on every CI run.
- Uploads and snapshot downloads **stream** from and to disk, and realtime logs and status arrive through an **iterator** or `async for`.
- **One error type**, `SquareCloudAPIError`, for every API error, network failure and failed local check.

[Documentation](https://docs.squarecloud.app/en/sdks/py/client) · [Releases](https://github.com/squarecloudofc/sdk-api-py/releases) · [Migration guide](MIGRATION.md)

## Installation

```bash
pip install squarecloud-api
uv add squarecloud-api
poetry add squarecloud-api
```

Requires Python 3.11 or newer.

## API key

Create one at [squarecloud.app/account/security](https://squarecloud.app/account/security). You can limit a key to scopes, such as `apps:read` or `apps:deploy`, and to specific applications or databases. A call outside those limits raises `SquareCloudAPIError` with 403 `MISSING_SCOPE` or `RESOURCE_NOT_ALLOWED`, and list calls return only the resources the key can see. An unknown, revoked or expired key gets 401 `ACCESS_DENIED`.

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

The same calls with `await`:

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
| `api_key` | required | Sent as is in `Authorization`. An empty or blank key raises `ValueError`. |
| `base_url` | `BASE_URL` = `https://api.squarecloud.app/v2` | A trailing `/` is removed. |
| `timeout` | `30.0` | Seconds each connect, send or read may take. A value of 0 or less disables every timeout, including the 120-second minimum of slow calls. See [Retries, timeouts and rate limits](#retries-timeouts-and-rate-limits). |
| `max_retries` | `2` | A negative value counts as 0. |
| `transport` | `HTTPTransport(timeout)` | Your own HTTP transport. See [Custom transport](#custom-transport). |
| `user_agent` | `squarecloud-sdk-py/<version>` | Replaces the whole `User-Agent` header. |

`AsyncSquareCloud` takes the same arguments. Both clients are safe to share between threads. Call `close()`, or use `with` or `async with`, to close their connections. The version is `squarecloud.__version__`.

### Custom transport

`transport=` accepts any callable `transport(method, url, headers, body, timeout, stream)` that returns an object with `status`, `read()`, `readline()` and `close()`. An `http.client.HTTPResponse` already has that shape. Use it for proxies, tracing or tests.

- `body` is `bytes`, an iterable of `bytes` chunks with `Content-Length` already in `headers`, or `None`.
- `timeout` is how many seconds each connect, send or read may take, raised to 120 for the calls the API holds open. It is `None` for uploads, large file writes and the realtime feed, so bound their connect yourself.
- `stream` means the caller reads the body bit by bit and may call `close()` from another thread to stop it.

The default `HTTPTransport(timeout)` bounds that connect for you. It asks for compressed responses on every call except the streamed ones, which are the realtime feed and snapshot downloads.

### Logging

The SDK logs each request at `DEBUG` on the `squarecloud` logger, with the method, path and status but never a body or a key. It attaches only a `NullHandler`:

```python
import logging

logging.basicConfig()
logging.getLogger('squarecloud').setLevel(logging.DEBUG)
```

## API

Every application id can also be the composite `'<appId>-<workspaceId>'`, to act on an application someone shared with you through a workspace. Optional arguments are keyword-only, except the `path` of `apps.files.list`.

| Group | Methods |
|---|---|
| `account` | `me()`, `snapshots(*, scope=None)` |
| `service` | `status()`, for which the API does not check the key, although the client still needs a non-empty one |
| `ai` | `chat(request)`, OpenAI-compatible and without streaming |
| `apps` | `create(file)`, `get(id)`, `delete(id)`, `status_all(*, workspace_id=None)`, `status(id, *, raw=False)`, `start(id)`, `stop(id)`, `restart(id)`, `logs(id)`, `metrics(id, *, range=None)`, `realtime(id)`, `domains()`, `load_balancers()`, `commit(id, file, *, path=None, filename=None)` |
| `apps.deploys` | `set_webhook(id, access_token)`, `link_github_app(id, repository, branch)`, `unlink_github_app(id)`, `list(id)`, `current(id)` |
| `apps.envs` | `get(id)`, `set(id, envs)`, `replace(id, envs)`, `delete(id, keys)` |
| `apps.files` | `list(id, path=None)`, `read(id, path)` → `bytes`, `write(id, path, content)`, `move(id, path, to)`, `delete(id, path)` |
| `apps.snapshots` | `list(id)`, `create(id)`, `restore(id, name, version_id)` → `{'pending': bool}`, `restore_state(id)` |
| `apps.network` | `analytics(id, start, end, **filters)`, `errors(id, start, end, *, include_4xx=False)`, `logs(id, start, end)`, `performance(id, start, end)`, `dns(id)`, `set_domain(id, domain)`, `purge_cache(id)` |
| `databases` | `create(name, *, type, version, memory)`, `get(id)`, `update(id, *, name=None, ram=None)`, `delete(id)`, `start(id)`, `stop(id)`, `status(id, *, raw=False)`, `metrics(id, *, range=None)`, `status_all()`, `certificate(id)`, `reset_credentials(id, 'password' \| 'certificate')` → the new password, or `''` |
| `databases.snapshots` | `list(id)`, `create(id)`, `restore(id, name, version_id)` → `{'pending': bool}`, `restore_state(id)` |
| `workspaces` | `create(name)`, `list()`, `get(id)`, `delete(id)`, `leave(id)` |
| `workspaces.members` | `add(workspace_id, code, group)`, `update(workspace_id, member_id, group)`, `remove(workspace_id, member_id)`, `invite_code()` |
| `workspaces.apps` | `add(workspace_id, app_id)`, `remove(workspace_id, app_id)` |
| client | `download_snapshot(url, dest)`, `close()` |

`AsyncSquareCloud` has the same groups and methods, and each one returns a coroutine that runs the sync call in a worker thread. The exceptions are `close()`, which is sync, and `apps.realtime(id)`, which returns an `AsyncRealtime` for `async for`.

Responses are `TypedDict`s from `squarecloud.types`. They are plain dicts that keep any field the API adds later. Field names are the API's own, such as `created_at`, `content_type` and `include_4xx`, so the [API reference](https://docs.squarecloud.app/api-reference) applies as is. A string result is never `None`. It is `''` when the API sends nothing.

- `start` and `end` take an ISO 8601 string, which is sent as is, or a `datetime`, which is sent in UTC. A naive `datetime` is read as local time.
- The `analytics` filters are keyword-only: `country`, `ip`, `path`, `status`, `os`, `browser`, `protocol`, `referer`, `provider`, `content_type` and `bot`. `provider` takes the `'NAME (ASN)'` form that the `providers` buckets report, such as `provider='GOOGLE (15169)'`. An invalid filter is 400 `INVALID_FILTER`.
- `apps.network.analytics`, `errors` and `performance` return `None` for a window with no traffic.
- `metrics()` returns points newest first. By default it covers 24 hours with one point every 5 minutes, or every 10 minutes for applications below 512 MB. `range='7d'` gives hourly points with the hour's peaks in `cpu_max` and `ram_max` on Pro and Enterprise plans, for databases and for applications of 512 MB or more. Other plans and smaller applications get the 24-hour answer without an error, and an unknown `range` is 400 `INVALID_PARAMETERS`. `disk` (bytes read and written, like `net`) and `storage` are `None` on a point without a reading.
- `status()` formats `cpu` and `ram` as strings such as `'120.4MB'`. With `raw=True` they are numbers.
- An id that is empty, `.` or `..` fails locally with `INVALID_ID` before anything is sent, because it would address a different resource.

## Usage

### Uploads

`apps.create` and `apps.commit` take a path, `bytes` or a binary file object, and stream it, so a path or a seekable file is never loaded into memory. A commit unpacks a `.zip` into `path`, the application root by default. Any other file lands at `path/<filename>`. The filename is `filename=`, else the file's own name, else `app.zip` on create and `commit.zip` on commit. A file over 100 MB fails locally with `FILE_TOO_LARGE` before anything is sent. Uploads have no timeout.

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

A `str` is sent as text. `bytes` are sent base64-encoded, which keeps binary content intact and takes about 1.33 times the size on the wire. Empty content (`''` or `b''`) creates an empty file. Content over 10 MB fails locally with `FILE_TOO_LARGE`, and content over 1 MiB is sent without a timeout, like an upload. Content the API cannot decode is 400 `INVALID_CONTENT`. `read` always asks for base64 and returns the decoded `bytes`, and a file over 10 MB is 413 `FILE_TOO_LARGE`. `list` of a missing directory is 404 `FILE_NOT_FOUND`, and a protected path is 403 `BLOCKED_PATH`. Paths are at most 256 characters.

### Snapshots

`create` returns `{'pending': True}` while the API is still generating the snapshot, which it signals with HTTP 202 `SNAPSHOT_PROCESSING`. The snapshot then appears in `list` on its own, usually within 2 minutes. Poll `list` and do not call `create` again, because it allows one call every 180 seconds and each call counts against your plan's daily snapshot quota. An API key without `snapshots:read` gets `{'pending': False}` with `url` and `key` set to `''`.

`restore` returns `{'pending': True}` when the restore is not done after about 90 seconds, which the API signals with HTTP 202 `SNAPSHOT_RESTORE_PROCESSING`. The restore keeps running in the background. Follow it with `restore_state` and do not call `restore` again. `restore_state` reports `queued` or `running` with the current `step`, then `success`, or `error` with a `code`, for 1 hour after the restore ends, and `none` when there is no recent restore. It allows 30 calls per minute.

```python
import time

snapshot = client.apps.snapshots.create(app_id)
if not snapshot['pending']:
    client.download_snapshot(snapshot['url'], 'backups/')  # -> backups/<name>.zip

latest = max(client.apps.snapshots.list(app_id), key=lambda s: s['modified'])
client.download_snapshot(latest['url'], 'backups/')

restored = client.apps.snapshots.restore(app_id, latest['name'], latest['version_id'])
if restored['pending']:
    state = client.apps.snapshots.restore_state(app_id)
    while state['state'] in ('queued', 'running'):
        time.sleep(5)
        state = client.apps.snapshots.restore_state(app_id)
    print(state['state'], state.get('code', ''))  # success, or error with a code
```

Each listed snapshot carries the API's `version_id`, which `restore` needs, and a signed download `url`, both passed through as sent. The `url` from `list` and `create` is valid for 1 hour. When snapshot storage cannot answer, a listing fails with 503 `SNAPSHOTS_UNAVAILABLE`, so try again in about 30 seconds.

A restore can fail with 400 `MISSING_PARAMETERS`, `INVALID_SNAPSHOT_ID` or `INVALID_VERSION_ID`, and on databases also with `SNAPSHOT_DATABASE_MISMATCH`. It can fail with 404 `APP_NOT_FOUND`, `DATABASE_NOT_FOUND`, `SNAPSHOT_NOT_FOUND`, `SNAPSHOT_RESTORE_FAILED`, `SNAPSHOT_CORRUPT`, `RESTORE_INTERRUPTED` or `CONTAINER_NOT_FOUND`, with 409 `RESTORE_IN_PROGRESS` or `SNAPSHOT_IN_PROGRESS`, with 413 `PAYLOAD_TOO_LARGE`, and with 503 `CLUSTER_MAINTENANCE_TRY_LATER`, which snapshot `create` can return too.

`download_snapshot` never sends your API key with the download. It streams to a `.part` file next to the target and renames it once complete, and each read waits at most `timeout`.

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

Every event has `event`, `data` (the raw text of the event) and `id`. The HTTP status is checked before any event, so 429 `REALTIME_MAX_CONNECTIONS` raises right away. If the connection drops, or the API hands the feed over with `REALTIME_RECONNECT`, the feed reopens on its own up to 3 times in a row, and a `logs` or `status` event resets that count. It opens at most once every 5.5 seconds, to stay under the API's limit of one open every 5 seconds. Past 3 reopens it raises `NETWORK_ERROR`.

The client's `timeout` applies only until the feed opens. The loop ends when the API closes the feed after its 10-minute limit, on `REALTIME_DISCONNECTED`, or when you call `stream.close()`, which is safe from any thread and also stops a wait. With `AsyncSquareCloud`, use `async with client.apps.realtime(app_id) as stream:` and `async for event in stream:`. Each account can have up to 5 open feeds, and each application up to 30.

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

Linking needs the `apps:deploy` scope and a GitHub App installation on your account, or it fails with 403 `GITHUB_NOT_CONNECTED`. The repository must belong to a GitHub App installation that your connected GitHub account holds, or it fails with 403 `REPOSITORY_NOT_AVAILABLE`. That account also needs write access to the repository, or it fails with 403 `REPOSITORY_PERMISSION_REQUIRED`. 502 `FAILED_TO_FETCH` means GitHub did not confirm the branch, and it is safe to try again.

A repository and branch can be linked to only one application across all accounts. Another link fails with 409 `REPOSITORY_BRANCH_ALREADY_CONFIGURED`, and the other application's id appears in `message` only when that application is yours. To link again, unlink first, or the call fails with 400 `GIT_ALREADY_CONFIGURED`. Unlinking without a link fails with 400 `GIT_NOT_CONFIGURED`. Link and unlink share a limit of 3 calls per minute.

## Errors

Every API and network failure raises `SquareCloudAPIError` with `status`, `code`, `message`, `method`, `path` and `cause`. The `path` looks like `'/v2/apps/...'` and never includes the query string. Local file problems, such as a missing upload path or a download destination you cannot write to, raise `OSError`.

```python
from squarecloud import SquareCloudAPIError

try:
    client.apps.start(app_id)
except SquareCloudAPIError as e:
    print(e)  # POST /v2/apps/<id>/start: HTTP 404 APP_NOT_FOUND
    if e.code == 'MISSING_SCOPE':
        ...
```

- When no response arrives, `status` is `0` and `code` is `NETWORK_ERROR`, with the original exception in `cause`, or `TIMEOUT`.
- When a local check stops the call before anything is sent, `status` is `0` and `code` is `FILE_TOO_LARGE`, or `INVALID_ID` for an id that is empty, `.` or `..`.
- `message` is the server's explanation, or `''` when it sent only a code. A body without a code, such as a proxy page or a failed snapshot download, gives `UNKNOWN_ERROR` with the server's message when it sent one and `HTTP <status>` otherwise. A successful response whose body is not JSON gives `UNKNOWN_ERROR` with `Invalid JSON in HTTP <status> response`.
- A refused start, stop or restart is a 409 with only a code, so `message` is `''`. The code is `CONTAINER_ALREADY_STARTED`, `CONTAINER_ALREADY_STOPPED`, `CONTAINER_TEMPORARILY_SUSPENDED` (applications only), `CONTAINER_NOT_FOUND`, `CONTAINER_INSUFFICIENT_DISK_SPACE`, `CONTAINER_NETWORK_CONFLICT`, `ACTION_FAILED` or `RESTORE_IN_PROGRESS`. These are errors, so check `e.code` when a resource that is already started or stopped is fine for you.
- 409 `RESTORE_IN_PROGRESS` also answers a delete, start, stop, restart or snapshot `create` while a restore runs. Try again when the restore ends.
- A successful response whose body is `{"status": "error"}` also raises. The 202 answers `SNAPSHOT_PROCESSING` and `SNAPSHOT_RESTORE_PROCESSING` are not errors and return `{'pending': True}`.
- Errors from `ai.chat()`, including authentication, 429 and 503, carry the lowercase `code` of the OpenAI format, such as `access_denied`, `upgrade_required`, `rate_limit_exceeded`, `server_overloaded` or `database_unavailable`, or its `type` when there is no code.
- The `SquareCloudAPIError` docstring lists every known API code. The API can add codes, so treat an unknown code as a generic failure of its HTTP status.
- `str(e)` is `<METHOD> <path>: HTTP <status> <CODE>: <message>`. The `HTTP <status>` part is left out when the status is `0`, and the `: <message>` part when the message is empty.

## Retries, timeouts and rate limits

- **Timeouts.** `timeout`, 30 seconds by default, applies to each connect, send and read. Calls the API holds open wait at least 120 seconds: `start`, `stop` and `restart` of applications and databases, `databases.create`, and snapshot `create` and `restore`. So does `ai.chat()`, which answers within 90 seconds or fails with 503 `server_overloaded`. A larger `timeout` wins, and a `timeout` of 0 or less disables every timeout, including that minimum. Uploads and `files.write` calls over 1 MiB have no timeout, and `realtime()` is timed only until it opens.
- **Retries.** The SDK retries only what is safe to repeat, up to `max_retries` times, which is 2 by default. It retries network errors on `GET`, including a body cut off mid-read, realtime opens, and `download_snapshot()` before the download starts. It also retries 503 `UPLOAD_BUSY` and `ANALYTICS_BUSY` on any method, and 503 `DATABASE_UNAVAILABLE` on `GET`. Each wait is 500 ms × 2ⁿ, where n counts the retries from 0, capped at 8 seconds and randomly shortened by up to half.
- **Never retried.** Timeouts, any 429, the AI's 503 `server_overloaded` (safe for you to retry), 503 `SNAPSHOTS_UNAVAILABLE` and `CLUSTER_MAINTENANCE_TRY_LATER`, and 409 `RESTORE_IN_PROGRESS`, `SNAPSHOT_IN_PROGRESS` and `ENV_BUSY`. `ENV_BUSY` means another write to the environment variables is in progress. `DATABASE_UNAVAILABLE` is not retried on other methods because the change may already have been applied, so retrying an idempotent call such as `files.write`, `envs.replace` or `stop` is up to you.
- **Rate limits.** Every account has a global limit of requests per minute, set by its plan ([values](https://docs.squarecloud.app/en/api-reference/limitations-and-restrictions)). Going over it, or over the limit of a single call, returns 429 `RATE_LIMITED` or `KEEP_CALM`. `RATE_LIMITED` can block the account, API key or IP for about 30 minutes, and it is also the limit of the `apps.network` calls and of `account.snapshots()`. `RATE_LIMIT` and `RATE_LIMIT_EXCEEDED` are its deprecated names. The API sends no `Retry-After`, which is why the SDK never retries a 429.

## Development

```bash
uv sync
uv run ruff format --check && uv run ruff check && uv run mypy && uv run pytest   # offline
uv build
```

The offline suites (`tests/test_transport.py`, `tests/test_http.py`, `tests/test_streams.py`, `tests/test_conformance.py`, `tests/test_surface.py`) use a mock transport or a loopback server and never reach the API. The live suite runs all 69 operations against the real API:

```bash
SQUARECLOUD_API_KEY=... uv run pytest -m live -s
```

> **Warning:** the live suite creates and deletes real resources on the key's account: an application, a database and a workspace named `sdk-live-py-<timestamp>`. It is skipped without `SQUARECLOUD_API_KEY` and never runs in CI. Requests are spaced 2.1 seconds apart. Run the JS, Python and Go live suites one after another, never at the same time.

## Contributing

Issues and pull requests are welcome at [squarecloudofc/sdk-api-py](https://github.com/squarecloudofc/sdk-api-py).

## License

MIT, see [LICENSE](LICENSE).

## Authors

Maintained by [Square Cloud](https://squarecloud.app).

Contributors:

- Robert Nogueira ([@robert-nogueira](https://github.com/robert-nogueira))
- Jhonatan Jeferson ([@Jhonatan-Jeferson](https://github.com/Jhonatan-Jeferson))
