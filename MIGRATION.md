# Migrating from v4 to v5

v5 is a rewrite. The SDK is now synchronous by default, with an `await` client next to it. It has zero dependencies, groups its methods by resource, returns plain dicts typed as `TypedDict`, and raises a single exception type. It covers all 69 operations of the Square Cloud API.

## At a glance

| v4 | v5 |
|---|---|
| `await client.x(...)`, async only | `client.group.x(...)`, or `await async_client.group.x(...)` |
| Frozen dataclasses (`status.ram`) | `TypedDict`, a plain dict (`status['ram']`). Unknown fields are kept instead of raising `TypeError` |
| `Application` objects (`app.start()`, `app.cache`) | Plain data plus ids, as in `client.apps.start(app_id)`. There is no cache |
| About 25 exception classes (`NotFoundError`, `TooManyRequests`, `FewMemory`, ...) | `SquareCloudAPIError` with `.status`, `.code`, `.message`, `.method`, `.path` (`'/v2/...'`) and `.cause` |
| `squarecloud.File(path)` | Pass a path, `bytes` or a binary file object directly |
| Optional arguments by position | Optional arguments are keyword-only, as in `status(id, raw=True)`, `commit(id, file, path=...)` and `databases.create(name, type=, version=, memory=)` |
| Request listeners (`@client.on_request`), capture listeners, `avoid_listener`, `update_cache` | Removed. Use the `squarecloud` logger at DEBUG level or a custom `transport=` |
| `aiohttp` and `typing-extensions` dependencies | None |
| Python `>=3.13,<3.15` | Python `>=3.11`, with no upper bound |

## Construction and options

| v4 | v5 |
|---|---|
| `squarecloud.Client(api_key, log_level=...)` | `SquareCloud(api_key, *, base_url=BASE_URL, timeout=30.0, max_retries=2, transport=None, user_agent=...)`, or `AsyncSquareCloud(...)` with the same arguments |
| `log_level=` and a colored handler attached on import | `logging.getLogger('squarecloud')` with a `NullHandler`. Configure it yourself |
| `aiohttp` defaults of 5 minutes per request and 90 seconds between realtime reads | `timeout` in seconds for each connect, send or read, with a 120-second minimum for slow calls and AI calls. A `timeout` of 0 or less disables every timeout |
| No retries | `max_retries` (2) for the failures that are safe to repeat. A 429 is never retried |
| Hardcoded `User-Agent` | `user_agent=` replaces the header. The default is `squarecloud-sdk-py/<version>` |
| A new session per request | `close()`, `with` or `async with` closes the reused connections |

## Method by method

| old (v4 `Client`) | new (v5 `SquareCloud`) | notes |
|---|---|---|
| `user()` | `account.me()['user']` | `me()` also returns `applications` and `databases` |
| `all_apps()` | `account.me()['applications']` | |
| `app(app_id)` | `apps.get(app_id)` | Now reads the application directly, so it works with the workspace id `'<appId>-<workspaceId>'` |
| `user_snapshots(scope)` | `account.snapshots(*, scope=None)` | `scope` is keyword-only. Items carry the API's `version_id` and signed `url` |
| `service_status()` | `service.status()` | |
| `upload_app(File(path))` | `apps.create(path)` | Streams from disk and returns `AppCreated`. Its `domain` is a website's full host, and there is no `subdomain` |
| `delete_app(id)` | `apps.delete(id)` | Returns `None` |
| `all_apps_status()` | `apps.status_all(*, workspace_id=None)` | Stopped applications are no longer dropped |
| `app_status(id)` | `apps.status(id, *, raw=False)` | `raw=True`, keyword-only, returns numbers |
| `start_app` / `stop_app` / `restart_app` | `apps.start` / `apps.stop` / `apps.restart` | Return `None` |
| `get_logs(id)` | `apps.logs(id)` | Returns the `str` |
| `app_metrics(id)` | `apps.metrics(id)` | |
| `realtime(id)`, an async generator of each `data:` line, decoded from JSON when possible | `apps.realtime(id)` | An iterator of `{'event', 'data', 'id'}` with the raw `data` text, plus `stream` and `line` on log events and the merged `status` on status events. It reconnects on its own (see Behavior changes). The feed has no read timeout, where v4 gave up after 90 seconds without data, so stop it with `close()` |
| `all_domains()` | `apps.domains()` | |
| `load_balancers()` | `apps.load_balancers()` | |
| `commit(id, File(path))` | `apps.commit(id, file, *, path=None, filename=None)` | `path` is the destination directory and is keyword-only. `filename` names a file that is not a zip, and `bytes` default to `commit.zip` |
| `github_integration(id, access_token)` | `apps.deploys.set_webhook(id, access_token)` | |
| `last_deploys(id)` | `apps.deploys.list(id)` | Events include `source`, `branch` and `files`. A failed deploy ends with `state='error'` plus `code` and `message` |
| `current_app_integration(id)` | `apps.deploys.current(id)` | Returns `{'app'?, 'webhook'?}` instead of the webhook string |
| `get_app_envs` / `set_app_envs` / `overwrite_app_envs` / `delete_app_envs` | `apps.envs.get` / `set` / `replace` / `delete` | |
| `clear_app_envs(id)` | `apps.envs.replace(id, {})` | |
| `app_files_list(id, path)` | `apps.files.list(id, path=None)` | Entries are the API's `FileEntry`, without a computed `path` or `app_id`. A missing directory raises 404 `FILE_NOT_FOUND` instead of returning `[]`, and a protected one raises 403 `BLOCKED_PATH` |
| `read_app_file(id, path)` → `BytesIO` | `apps.files.read(id, path)` → `bytes` | Fetched base64-encoded and decoded. A file over 10 MB is 413 `FILE_TOO_LARGE` |
| `create_app_file(id, File(...), path)` | `apps.files.write(id, path, content)` | A `str` is sent as text and `bytes` base64-encoded, so binary content arrives intact. The path is sent as given, without an extra `/`. Empty content (`''` or `b''`) creates an empty file |
| `move_app_file(id, origin, dest)` | `apps.files.move(id, path, to)` | |
| `delete_app_file(id, path)` | `apps.files.delete(id, path)` | |
| `snapshot(id)` → `Snapshot` | `apps.snapshots.create(id)` | Returns `{'pending': True}` on a 202 instead of raising. Then poll `list`, and do not create it again |
| `all_app_snapshots(id)` | `apps.snapshots.list(id)` | Items carry the API's `version_id` and signed download `url`, passed through as sent |
| `restore_snapshot('app', id, snapshot_id, version_id)` | `apps.snapshots.restore(id, name, version_id)` | `name` and `version_id` come from a `list` item |
| `restore_snapshot('database', id, ...)` | `databases.snapshots.restore(id, name, version_id)` | `name` and `version_id` come from a `list` item |
| `Snapshot.download(path)` | `client.download_snapshot(url, dest)` | Streams the zip itself, where v4 wrapped it in another zip |
| `domain_analytics(id, start=, end=, ...)` | `apps.network.analytics(id, start, end, *, country=, ...)` | The API requires `start` and `end`. The filters are keyword-only |
| `network_errors(id, start, end, include_4xx)` / `network_logs` / `network_performance` | `apps.network.errors(id, start, end, *, include_4xx=False)` / `logs` / `performance` | `analytics`, `errors` and `performance` return `None` for a window without data |
| `dns_records(id)` | `apps.network.dns(id)` | |
| `set_custom_domain(id, custom_domain)` | `apps.network.set_domain(id, domain)` | v4 never sent the domain |
| `purge_cache(id)` | `apps.network.purge_cache(id)` | |
| `link_github_app(id, repository_name, repository_branch)` | `apps.deploys.link_github_app(id, repository, branch)` | Now works with an API key that has the `apps:deploy` scope. Returns the `LinkedRepository` (`{id, full_name, branch}`) instead of the raw dict. Fails with 403 `GITHUB_NOT_CONNECTED` without a GitHub App installation |
| `unlink_github_app(id)` | `apps.deploys.unlink_github_app(id)` | Returns `None`. Fails with 400 `GIT_NOT_CONFIGURED` when nothing is linked |
| `create_database(name, memory, type, version=None)` | `databases.create(name, type=, version=, memory=)` | Keyword-only. `version` is required, and a major version such as `'8'` works |
| `get_database_info(id)` | `databases.get(id)` | |
| `edit_database(id, name, memory)` | `databases.update(id, name=, ram=)` | v4 sent `memory`, which the API ignored |
| `delete_database` / `start_database` / `stop_database` | `databases.delete` / `start` / `stop` | |
| `get_database_status(id)` | `databases.status(id, *, raw=False)` | |
| `all_databases_status()` | `databases.status_all()` | |
| `database_metrics(id)` | `databases.metrics(id)` | |
| `get_database_certificate(id)` → `Certificate` | `databases.certificate(id)` → base64 `str` | `base64.b64decode(...)` gives the PEM |
| `reset_database_password(id)` | `databases.reset_credentials(id, 'password')` | Returns the new password |
| `reset_database_certificate(id)` | `databases.reset_credentials(id, 'certificate')` | Returns `''` |
| `all_database_snapshots(id)` / `database_snapshot(id)` | `databases.snapshots.list(id)` / `create(id)` | Items carry `version_id` and `url`, as for applications |
| `create_workspace(name)` | `workspaces.create(name)` | Returns `{id, name}` in one request |
| `all_workspaces()` / `get_workspace(id)` | `workspaces.list()` / `workspaces.get(id)` | v4 rewrote each application `id` to the composite `'<appId>-<workspaceId>'`. v5 returns the API's own id, so build the composite yourself with `f"{app['id']}-{workspace['id']}"` |
| `delete_workspace` / `leave_workspace` | `workspaces.delete` / `workspaces.leave` | |
| `add_member_to_workspace(ws, invite_code, permissions)` | `workspaces.members.add(ws, code, group)` | |
| `modify_member_permissions(ws, user_id, permissions)` | `workspaces.members.update(ws, member_id, group)` | |
| `remove_member_from_workspace(ws, user_id)` | `workspaces.members.remove(ws, member_id)` | |
| `get_invite_code()` | `workspaces.members.invite_code()` | |
| `add_app_to_workspace` / `remove_app_from_workspace` | `workspaces.apps.add` / `workspaces.apps.remove` | |
| — | `ai.chat(request)` | New. `request` is the OpenAI-style body, such as `{'messages': [...], 'model': ...}` |
| `client.api_key` | Removed | Keep your own reference to the key |
| `on_request(endpoint)`, `Application.capture(endpoint)` | Removed | See the listeners row in [At a glance](#at-a-glance) |
| `squarecloud.utils.ConfigFile` | Removed | Write the `squarecloud.app` file yourself, as `KEY=value` lines |

`Application` methods map to the same calls with the id. For example, `app.logs()` becomes `client.apps.logs(app.id)`, and `app.files_list(path)` becomes `client.apps.files.list(app.id, path)`.

## Types

Responses are `TypedDict`s in `squarecloud.types`, with the same names as in the JS and Go SDKs: `Account`, `User`, `Plan`, `AppSummary`, `DatabaseSummary`, `App`, `AppCreated`, `StatusListItem`, `RuntimeStats`, `MetricPoint`, `AppDomain`, `LoadBalancers`, `DeployEvent`, `DeployCurrent`, `DeployRepository`, `LinkedRepository`, `EnvVars`, `FileEntry`, `Snapshot`, `SnapshotCreated`, `SnapshotScope`, `AnalyticsFilters`, `NetworkAnalytics`, `NetworkErrors`, `NetworkLog`, `NetworkPerformance`, `DNSRecord`, `Database`, `DatabaseCreated`, `DatabaseType`, `Workspace`, `WorkspaceCreated`, `WorkspaceGroup`, `ServiceStatus`, `ServiceEntry`, `ChatRequest`, `ChatMessage`, `ChatCompletion`, `RealtimeEvent` and `RealtimeStatus`. They replace the v4 `data/*` dataclasses, such as `UserData`, `StatusData` and `AppData`. `squarecloud.Response` is now the response protocol of a custom transport (see the README). The v4 `Response` that mutations returned is gone, and mutations now return `None`.

## Errors

| v4 | v5 |
|---|---|
| `AuthenticationFailure` | `e.status == 401` (`ACCESS_DENIED`, also for an expired key) |
| `NotFoundError`, `ApplicationNotFound` | `e.status == 404` (`APP_NOT_FOUND`, `WORKSPACE_NOT_FOUND`, ...) |
| `BadRequestError` and the `InvalidConfig` family | `e.status == 400`, then check `e.code` |
| `TooManyRequests` | `e.status == 429` (`RATE_LIMITED`, `KEEP_CALM`) |
| `FewMemory`, never raised because the API sends `INSUFFICIENT_MEMORY` | `e.code == 'INSUFFICIENT_MEMORY'` |
| `InvalidDomain`, for the `REGEX_VALIDATION` code the API no longer sends | `e.code == 'INVALID_DOMAIN'` |
| `RequestError` for 403 and 503 | `e.code` in `MISSING_SCOPE`, `RESOURCE_NOT_ALLOWED`, `BLOCKED_PATH`, `UPLOAD_BUSY`, ... |
| `aiohttp` exceptions leaking | `e.status == 0` with `e.code` `NETWORK_ERROR` or `TIMEOUT`, and the original exception in `e.cause` |
| — | `e.status == 0` with `FILE_TOO_LARGE` or `INVALID_ID`, for local checks that stopped the call before anything was sent |
| A proxy HTML page or another body that is not JSON leaking | `UNKNOWN_ERROR` with the real status and the message `HTTP <status>`, or `Invalid JSON in HTTP <status> response` on a success status |

`str(e)` is `'<METHOD> <path>: HTTP <status> <CODE>: <message>'`. The `HTTP <status>` part is left out when the status is `0`, and the `: <message>` part when the message is empty. `e.message` is `''` when the server sent only a code.

## Behavior changes

- Optional arguments are keyword-only: `account.snapshots(scope=)`, `apps.status_all(workspace_id=)`, `apps.status(id, raw=)`, `databases.status(id, raw=)`, `apps.commit(id, file, path=, filename=)`, `apps.network.errors(..., include_4xx=)`, the `apps.network.analytics(...)` filters, `databases.update(id, name=, ram=)` and `databases.create(name, type=, version=, memory=)`. The optional `path` of `apps.files.list` stays positional.
- A successful response whose body is `{"status": "error"}` raises. A refused start or stop of an application or database is a 409 with only a code, such as `CONTAINER_ALREADY_STARTED` or `ACTION_FAILED`. A 202 `SNAPSHOT_PROCESSING` returns `{'pending': True}` instead of raising. Poll `list` then, and do not call `create` again.
- Optional query values that are unset or `''` are left out instead of being sent.
- String results are never `None`. `reset_credentials(id, 'certificate')` and a removed webhook return `''`.
- `apps.files.write` sends a `str` as text and `bytes` base64-encoded. Empty content creates an empty file, and content over 1 MiB is sent without a timeout. `apps.files.read` always asks for base64 and returns the decoded `bytes`.
- `apps.files.list` of a missing directory raises 404 `FILE_NOT_FOUND`.
- 503 `DATABASE_UNAVAILABLE` is retried on `GET` only, because on other methods the change may already have been applied. Retrying an idempotent call is up to you.
- The realtime feed yields `{'event', 'data', 'id', ...}` events. It reopens at most 3 times in a row, at most once every 5.5 seconds, and raises when an open fails.

## Async

v4 was async only. In v5, `SquareCloud` is synchronous and `AsyncSquareCloud` is its `await` counterpart. It has the same groups and methods, and each call runs in `asyncio.to_thread`, so the event loop is never blocked. The realtime feed becomes `async for`, fed by a background thread. Close it with `async with` or `close()`.

v4:

```python
client = squarecloud.Client(key)
status = await client.app_status(app_id)
print(status.ram)
async for data in client.realtime(app_id):
    print(data)
```

v5:

```python
async with squarecloud.AsyncSquareCloud(key) as client:
    status = await client.apps.status(app_id)
    print(status['ram'])
    async with client.apps.realtime(app_id) as stream:
        async for event in stream:
            print(event['data'])
```
