"""Clients for the Square Cloud API.

:class:`SquareCloud` is the synchronous client and :class:`AsyncSquareCloud`
is its asyncio counterpart. Both expose the same method groups.
"""

from __future__ import annotations

import contextlib
import http.client
import json
import os
import threading
from collections.abc import Callable, Generator, Iterable
from typing import Any
from urllib.parse import urlencode, urlsplit

from . import _wire, types
from ._transport import Body as Body
from ._transport import HTTPTransport, Response, Transport
from ._wire import (
    _BUSY,
    _CHUNK,
    _JSON,
    _api_error,
    _delay,
    _failed,
    _json,
    _LocalError,
    _network_error,
    log,
)
from ._wire import MAX_FILE_BYTES as MAX_FILE_BYTES
from ._wire import MAX_UPLOAD_BYTES as MAX_UPLOAD_BYTES
from ._wire import Time as Time
from ._wire import UploadFile as UploadFile
from .errors import SquareCloudAPIError
from .realtime import AsyncRealtime, Realtime
from .resources.account import AI, Account, AsyncAccount, AsyncAI, AsyncService, Service
from .resources.apps import Apps, AsyncApps
from .resources.apps import AsyncDeploys as AsyncDeploys
from .resources.apps import AsyncEnvs as AsyncEnvs
from .resources.apps import AsyncFiles as AsyncFiles
from .resources.apps import AsyncNetwork as AsyncNetwork
from .resources.apps import Deploys as Deploys
from .resources.apps import Envs as Envs
from .resources.apps import Files as Files
from .resources.apps import Network as Network
from .resources.databases import AsyncDatabases, Databases
from .resources.snapshots import AsyncSnapshots as AsyncSnapshots
from .resources.snapshots import Snapshots as Snapshots
from .resources.workspaces import AsyncMembers as AsyncMembers
from .resources.workspaces import AsyncWorkspaceApps as AsyncWorkspaceApps
from .resources.workspaces import AsyncWorkspaces, Workspaces
from .resources.workspaces import Members as Members
from .resources.workspaces import WorkspaceApps as WorkspaceApps

# The `X as X` imports above, and USER_AGENT below, keep every name of the
# single-module v5.0 client importable from here. They stay out of __all__.
__all__ = [
    'BASE_URL',
    'AsyncRealtime',
    'AsyncSquareCloud',
    'HTTPTransport',
    'Realtime',
    'Response',
    'SquareCloud',
    'SquareCloudAPIError',
    'Transport',
    '__version__',
    'types',
]

# The single version source: pyproject.toml reads it (tool.hatch.version).
__version__ = '5.1.0'

BASE_URL = 'https://api.squarecloud.app/v2'
USER_AGENT = f'squarecloud-sdk-py/{__version__}'


class SquareCloud:
    """Synchronous client for the Square Cloud API.

    The methods are grouped by resource: ``account``, ``service``, ``ai``,
    ``apps``, ``databases`` and ``workspaces``. One client can be shared
    between threads, and each thread reuses its own connection. Call
    :meth:`close` when you are done, or use the client in a ``with`` block.

    Args:
        api_key: Your API key, created at
            https://squarecloud.app/account/security.
        base_url: The API address. A trailing ``/`` is removed.
        timeout: How many seconds each connect, send or read may take.
            Calls the API can hold open for a long time wait at least 120
            seconds: start, stop and restart, database creation, snapshot
            create and restore, and ``ai.chat``. A value of 0 or less
            disables every timeout, including that 120-second minimum.
        max_retries: How many times to retry a failure that is safe to
            repeat. Those are a network error on a ``GET`` request, 503
            ``UPLOAD_BUSY`` or ``ANALYTICS_BUSY`` on any request, and 503
            ``DATABASE_UNAVAILABLE`` on a ``GET`` request. Each attempt waits
            longer than the last. A timeout and a 429 are never retried. A
            negative value counts as 0.
        transport: A callable that sends the HTTP requests, for proxies,
            tracing or tests (see :class:`Transport`). Defaults to an
            :class:`HTTPTransport`.
        user_agent: The whole ``User-Agent`` header to send.

    Raises:
        ValueError: ``api_key`` is empty or contains only whitespace.
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
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError(
                'The API key is missing or empty. Create a key at '
                'https://squarecloud.app/account/security and pass it to the '
                'client.'
            )
        self._base_url = base_url.rstrip('/')
        # The base path (such as '/v2') prefixes the path of every error.
        self._base_path = urlsplit(self._base_url).path
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
        """Return the client for use in a ``with`` block."""
        return self

    def __exit__(self, *_: object) -> None:
        """Close the client when the ``with`` block ends."""
        self.close()

    def close(self) -> None:
        """Close the client's open connections.

        A custom transport is closed only when it has a ``close()`` method.
        """
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
        pending: bool = False,
        stream: bool = False,
        url: str | None = None,
        stop: threading.Event | None = None,
    ) -> Any:
        """Send one call and apply the retry policy.

        Network errors are retried on GET only, and timeouts never. 503
        UPLOAD_BUSY and ANALYTICS_BUSY are retried on any method. 503
        DATABASE_UNAVAILABLE is retried on GET only, because it can arrive
        after a mutation was applied. A 429 is never retried.

        ``min_timeout`` raises the timeout of a call the server holds open.
        A 2xx body of ``{status: 'error'}`` raises, except on ``raw`` routes
        (which have no envelope) and on a 202. The result is the decoded
        JSON body, or the open 2xx response when ``stream`` is set. With
        ``pending`` (snapshot create and restore), a 202 returns
        ``{'pending': True}`` whatever its body, and any other success
        returns ``{'pending': False, **response}``. Setting ``stop`` ends a
        retry wait at once and raises the error that caused it.
        """
        max_retries = self._max_retries
        if url is None:
            if any(s in ('', '.', '..') for s in path.split('/')[1:]):
                raise SquareCloudAPIError(
                    0,
                    'INVALID_ID',
                    'The id is empty, "." or "..", so the request was not sent. '
                    'Pass the id of the resource you want to reach.',
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
        else:  # Another host, such as a snapshot download: never send the key.
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
        path = urlsplit(url).path  # Errors report the full path, such as /v2/...
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
                    or isinstance(exc, TimeoutError)  # A timeout is never retried.
                ):
                    raise _network_error(exc, method, path) from exc
                log.debug('%s %s: %r, retrying', method, path, exc)
                _wire._sleep(_delay(attempt), stop)
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
            except ValueError as exc:  # A proxy's HTML page or a storage XML error.
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
                # A safety net: a 2xx {status: 'error'} is still a failure.
                raw or status == 202 or not _failed(data)
            ):
                if not pending:
                    return data
                if status == 202:
                    return {'pending': True}
                r = data.get('response') if isinstance(data, dict) else None
                return {'pending': False, **(r if isinstance(r, dict) else {})}
            error = _api_error(status, data, method, path)
            if (
                status == 503
                and attempt < max_retries
                and (
                    error.code in _BUSY
                    or (method == 'GET' and error.code == 'DATABASE_UNAVAILABLE')
                )
            ):
                _wire._sleep(_delay(attempt), stop)
                if stop is None or not stop.is_set():
                    attempt += 1
                    continue
            raise error

    def _r(self, method: str, path: str, **kwargs: Any) -> Any:
        """Call ``_request`` and return the ``response`` of its envelope."""
        data = self._request(method, path, **kwargs)
        return data.get('response') if isinstance(data, dict) else data

    def download_snapshot(self, url: str, dest: str | os.PathLike[str]) -> str:
        """Download a snapshot to a local file.

        The download is streamed to a temporary ``.part`` file that is
        renamed only once it is complete, so a failed download never
        replaces an earlier file. Your API key is not sent with it. Each
        read may wait up to the client's ``timeout``, and a network error
        before the download starts is retried like any ``GET``.

        Args:
            url: The snapshot's download ``url``, from a snapshot ``list``
                or ``create``. It is valid for 1 hour.
            dest: A file path, or a directory to keep the snapshot's own
                file name. A path that ends with a separator is created as a
                directory.

        Returns:
            The path of the file written.

        Raises:
            SquareCloudAPIError: The download failed. An error response,
                such as the one for an expired link, carries its HTTP status
                and the code ``UNKNOWN_ERROR`` when its body names no code.
            OSError: ``dest`` cannot be created or written.
        """
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


class AsyncSquareCloud:
    """Asyncio client for the Square Cloud API.

    It takes the same arguments and has the same groups and methods as
    :class:`SquareCloud`, but every call returns a coroutine. Each call runs
    the synchronous client in a worker thread, so it never blocks the event
    loop. :meth:`close` is the only synchronous method, and
    ``apps.realtime`` returns an :class:`AsyncRealtime` for ``async for``.
    Use the client in an ``async with`` block to close it at the end::

        async with AsyncSquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client:
            statuses = await client.apps.status_all()
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
        """Return the client for use in an ``async with`` block."""
        return self

    async def __aexit__(self, *_: object) -> None:
        """Close the client when the ``async with`` block ends."""
        self.close()

    def close(self) -> None:
        """Close the client's open connections.

        A custom transport is closed only when it has a ``close()`` method.
        """
        self._sync.close()

    async def download_snapshot(self, url: str, dest: str | os.PathLike[str]) -> str:
        """Download a snapshot to a local file.

        This is the async version of :meth:`SquareCloud.download_snapshot`,
        with the same arguments, result and errors.
        """
        import asyncio

        return await asyncio.to_thread(self._sync.download_snapshot, url, dest)
