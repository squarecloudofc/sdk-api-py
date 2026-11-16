"""The ``apps`` group and its nested ``deploys``, ``envs``, ``files`` and
``network`` groups. The ``snapshots`` group lives in :mod:`.snapshots`."""

from __future__ import annotations

import base64
import builtins
from collections.abc import Iterable
from typing import TYPE_CHECKING, Literal, Unpack, cast

from .. import types as t
from .._group import _aio, _AsyncGroup, _Group
from .._wire import (
    _NO_TIMEOUT_BYTES,
    _SLOW,
    MAX_FILE_BYTES,
    Time,
    UploadFile,
    _iso,
    _multipart,
    _q,
    _too_large,
)
from ..realtime import AsyncRealtime, Realtime
from .snapshots import AsyncSnapshots, Snapshots

if TYPE_CHECKING:
    from ..client import SquareCloud


class Apps(_Group):
    """Create, control and inspect your applications.

    Reach it as ``client.apps``. Its nested groups are ``deploys``,
    ``envs``, ``files``, ``snapshots`` and ``network``.

    Every ``app_id`` in this group and its nested groups is an application
    id. To act on an application that someone shared with you through a
    workspace, pass the composite id ``'<appId>-<workspaceId>'`` instead.
    """

    def __init__(self, client: SquareCloud) -> None:
        super().__init__(client)
        self.deploys = Deploys(client)
        self.envs = Envs(client)
        self.files = Files(client)
        self.snapshots = Snapshots(client, '/apps')
        self.network = Network(client)

    def create(self, file: UploadFile) -> t.AppCreated:
        """Upload a zip and create an application from it.

        The file is streamed, so a path or a seekable file is never loaded
        into memory. The upload has no timeout.

        Args:
            file: The zip, as a path, ``bytes`` or a binary file object.

        Returns:
            The new application with its id, name, memory, CPU and
            language. A website also gets its ``domain``.

        Raises:
            SquareCloudAPIError: ``FILE_TOO_LARGE`` with status 0 when the
                zip is over 100 MB. Nothing is sent in that case. 400
                ``INSUFFICIENT_MEMORY`` when your plan does not have enough
                free memory for the application.
            OSError: The path does not exist or cannot be read.
        """
        body, headers = _multipart(file, self._c._base_path + '/apps')
        return self._c._r('POST', '/apps', body=body, headers=headers, no_timeout=True)

    def get(self, app_id: str) -> t.App:
        """Return the application's name, owner, memory, language and domains.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
        """
        return self._c._r('GET', f'/apps/{_q(app_id)}')

    def delete(self, app_id: str) -> None:
        """Delete the application and release its custom domain.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Raises:
            SquareCloudAPIError: 409 ``RESTORE_IN_PROGRESS`` while a
                snapshot restore is running. Try again when it ends.
        """
        self._c._request('DELETE', f'/apps/{_q(app_id)}')

    def status_all(self, *, workspace_id: str | None = None) -> list[t.StatusListItem]:
        """Return whether each of your applications is running, and its usage.

        Stopped applications are included, without ``cpu`` and ``ram``.

        Args:
            workspace_id: List the applications of this workspace instead of
                your own.
        """
        return self._c._r('GET', '/apps/status', query={'workspaceId': workspace_id})

    def status(self, app_id: str, *, raw: bool = False) -> t.RuntimeStats:
        """Return the application's current CPU, memory, network and storage usage.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            raw: Return numbers instead of formatted strings such as
                ``'120.4MB'``. CPU is then a percentage, memory is in MB, and
                storage and network are in bytes.
        """
        return self._c._r(
            'GET',
            f'/apps/{_q(app_id)}/status',
            query={'rawData': 'true' if raw else None},
        )

    def start(self, app_id: str) -> None:
        """Start the application.

        The call waits at least 120 seconds for the answer, even when the
        client's ``timeout`` is shorter.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Raises:
            SquareCloudAPIError: A refused start is a 409 whose ``message``
                is empty and whose ``code`` is ``CONTAINER_ALREADY_STARTED``,
                ``CONTAINER_ALREADY_STOPPED``,
                ``CONTAINER_TEMPORARILY_SUSPENDED``, ``CONTAINER_NOT_FOUND``,
                ``CONTAINER_INSUFFICIENT_DISK_SPACE``,
                ``CONTAINER_NETWORK_CONFLICT``, ``ACTION_FAILED`` or
                ``RESTORE_IN_PROGRESS``. Check ``code`` when an application
                that is already running is fine for you. After
                ``RESTORE_IN_PROGRESS``, try again when the restore ends.
        """
        self._c._request('POST', f'/apps/{_q(app_id)}/start', min_timeout=_SLOW)

    def stop(self, app_id: str) -> None:
        """Stop the application.

        The call waits at least 120 seconds for the answer, even when the
        client's ``timeout`` is shorter.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Raises:
            SquareCloudAPIError: A refused stop is a 409 with the same codes
                as :meth:`start`, such as ``CONTAINER_ALREADY_STOPPED``.
        """
        self._c._request('POST', f'/apps/{_q(app_id)}/stop', min_timeout=_SLOW)

    def restart(self, app_id: str) -> None:
        """Restart the application by stopping it and starting it again.

        The call waits at least 120 seconds for the answer, even when the
        client's ``timeout`` is shorter.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Raises:
            SquareCloudAPIError: A refused restart is a 409 with the same
                codes as :meth:`start`.
        """
        self._c._request('POST', f'/apps/{_q(app_id)}/restart', min_timeout=_SLOW)

    def logs(self, app_id: str) -> str:
        """Return the application's most recent log output as one string.

        This is a short excerpt of standard output and standard error
        together, not a live feed. Use :meth:`realtime` to follow the logs
        as they arrive.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Returns:
            The log text, or ``''`` when there is none.
        """
        return str(
            (self._c._r('GET', f'/apps/{_q(app_id)}/logs') or {}).get('logs') or ''
        )

    def metrics(
        self, app_id: str, *, range: Literal['24h', '7d'] | None = None
    ) -> list[t.MetricPoint]:
        """Return the application's usage history, newest point first.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            range: ``'24h'``, the default, returns one point every 5
                minutes, or every 10 minutes for applications below 512 MB.
                ``'7d'`` returns hourly points with the hour's peaks in
                ``cpu_max`` and ``ram_max``. It needs a Pro or Enterprise
                plan and an application of 512 MB or more. Otherwise the API
                returns the 24-hour history without an error.

        Raises:
            SquareCloudAPIError: 400 ``INVALID_PARAMETERS`` for any other
                ``range``.
        """
        return self._c._r('GET', f'/apps/{_q(app_id)}/metrics', query={'range': range})

    def realtime(self, app_id: str) -> Realtime:
        """Return a live feed of the application's logs, status and events.

        The connection opens when you start iterating. Leave the ``with``
        block, or call ``close()`` from any thread, to stop it. See
        :class:`~squarecloud.Realtime` for the events, reconnects and
        limits.

        Example::

            with client.apps.realtime(app_id) as stream:
                for event in stream:
                    if event['event'] == 'logs':
                        print(event['line'])

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
        """
        return Realtime(self._c, f'/apps/{_q(app_id)}/realtime')

    def domains(self) -> list[t.AppDomain]:
        """Return every domain of your applications, custom domains first.

        Each item names the application, the hostname, and whether it is
        the default subdomain or a custom domain. Applications without a
        domain are left out.
        """
        return self._c._r('GET', '/apps/domains')

    def load_balancers(self) -> t.LoadBalancers:
        """Return your custom domains with the applications that serve each one.

        A domain served by two or more applications balances its traffic
        between them. ``limit`` is how many applications your plan lets
        share one domain.
        """
        return self._c._r('GET', '/apps/load-balancers')

    def commit(
        self,
        app_id: str,
        file: UploadFile,
        *,
        path: str | None = None,
        filename: str | None = None,
    ) -> None:
        """Upload a file or a zip into an existing application.

        A ``.zip`` is unpacked into ``path``. Any other file is placed at
        ``path/<filename>``. The file is streamed and the upload has no
        timeout.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            file: The file, as a path, ``bytes`` or a binary file object.
            path: The destination directory. Defaults to the application
                root.
            filename: The name to upload the file under. Defaults to the
                file's own name, or to ``'commit.zip'`` for ``bytes`` and
                unnamed streams.

        Raises:
            SquareCloudAPIError: ``FILE_TOO_LARGE`` with status 0 when the
                file is over 100 MB, in which case nothing is sent. 403
                ``BLOCKED_PATH`` when a workspace Maintainer sends one of the
                application's restricted files, such as an ``.env`` file or
                the configuration file.
            OSError: The path does not exist or cannot be read.
        """
        endpoint = f'/apps/{_q(app_id)}/commit'
        body, headers = _multipart(
            file, self._c._base_path + endpoint, filename, 'commit.zip'
        )
        self._c._request(
            'POST',
            endpoint,
            query={'path': path},
            body=body,
            headers=headers,
            no_timeout=True,
        )


class AsyncApps(_AsyncGroup):
    """The async version of :class:`Apps`, reached as ``client.apps``.

    Every method takes the same arguments as in :class:`Apps` and returns a
    coroutine, except :meth:`realtime`.
    """

    def __init__(self, sync: Apps) -> None:
        super().__init__(sync)
        self.deploys = AsyncDeploys(sync.deploys)
        self.envs = AsyncEnvs(sync.envs)
        self.files = AsyncFiles(sync.files)
        self.snapshots = AsyncSnapshots(sync.snapshots)
        self.network = AsyncNetwork(sync.network)

    create = _aio(Apps.create)
    get = _aio(Apps.get)
    delete = _aio(Apps.delete)
    status_all = _aio(Apps.status_all)
    status = _aio(Apps.status)
    start = _aio(Apps.start)
    stop = _aio(Apps.stop)
    restart = _aio(Apps.restart)
    logs = _aio(Apps.logs)
    metrics = _aio(Apps.metrics)
    domains = _aio(Apps.domains)
    load_balancers = _aio(Apps.load_balancers)
    commit = _aio(Apps.commit)

    def realtime(self, app_id: str) -> AsyncRealtime:
        """Return a live feed of the application's events for ``async for``.

        Use it in an ``async with`` block so that leaving the block closes
        it. It works like :meth:`Apps.realtime`.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
        """
        return AsyncRealtime(self._sync.realtime(app_id))


class Deploys(_Group):
    """Deploy an application from GitHub on every push.

    Reach it as ``client.apps.deploys``. Each ``app_id`` accepts the same
    ids as :class:`Apps`, including the composite id of a workspace application.
    """

    def set_webhook(self, app_id: str, access_token: str) -> str:
        """Set up or remove the webhook that deploys the application on push.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            access_token: A GitHub personal access token. Pass ``'@'`` to
                remove the webhook.

        Returns:
            The webhook URL, or ``''`` after a removal.

        Raises:
            SquareCloudAPIError: 400 ``INVALID_ACCESS_TOKEN`` when the token
                is not a GitHub personal access token.
        """
        r = self._c._r(
            'POST',
            f'/apps/{_q(app_id)}/deploy/webhook',
            json_body={'access_token': access_token},
        )
        return str((r or {}).get('webhook') or '')

    def link_github_app(
        self, app_id: str, repository: str, branch: str
    ) -> t.LinkedRepository:
        """Link a GitHub repository and branch through the Square Cloud GitHub App.

        Pushes to the branch then deploy the application. The call needs
        the ``apps:deploy`` scope. Linking and unlinking share a limit of 3
        calls a minute.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            repository: The repository as ``'owner/name'``.
            branch: The branch to deploy from.

        Returns:
            The linked repository, with its GitHub ``id``, ``full_name`` and
            ``branch``.

        Raises:
            SquareCloudAPIError: 400 ``GIT_ALREADY_CONFIGURED`` when the
                application is already linked, so unlink it first. 403
                ``GITHUB_NOT_CONNECTED`` when your account has no GitHub App
                installation. 403 ``REPOSITORY_NOT_AVAILABLE`` when none of
                your installations covers the repository. 403
                ``REPOSITORY_PERMISSION_REQUIRED`` when you have no write
                access to it. 409 ``REPOSITORY_BRANCH_ALREADY_CONFIGURED``
                when another application, of any account, already links the
                same repository and branch. Its id appears in ``message``
                only when that application is yours. 502
                ``FAILED_TO_FETCH`` when GitHub did not confirm the branch,
                which is safe to try again.
        """
        r = self._c._r(
            'POST',
            f'/apps/{_q(app_id)}/deploy/github-app',
            json_body={'repositoryName': repository, 'repositoryBranch': branch},
        )
        # ponytail: a 2xx without it, such as a body relayed from another
        # service, gives {} like the Go zero value instead of a KeyError.
        return cast(t.LinkedRepository, (r or {}).get('repository') or {})

    def unlink_github_app(self, app_id: str) -> None:
        """Remove the application's GitHub App link.

        The call needs the ``apps:deploy`` scope. Linking and unlinking share
        a limit of 3 calls a minute.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Raises:
            SquareCloudAPIError: 400 ``GIT_NOT_CONFIGURED`` when nothing is
                linked.
        """
        self._c._request('DELETE', f'/apps/{_q(app_id)}/deploy/github-app')

    def list(self, app_id: str) -> builtins.list[builtins.list[t.DeployEvent]]:
        """Return the application's recent Git deploys.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Returns:
            One list of events per deploy, which moves through ``pending``,
            ``clone``, ``commit`` and ``restarting`` to ``success``. A
            failed deploy ends with an ``error`` event that carries a
            ``code``, and a ``message`` when there are details.
        """
        return self._c._r('GET', f'/apps/{_q(app_id)}/deployments')

    def current(self, app_id: str) -> t.DeployCurrent:
        """Return the application's GitHub App link and deploy webhook.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Returns:
            ``app`` holds the linked repository and ``webhook`` the webhook
            URL. Each key is present only when it is set, so the result is
            ``{}`` when nothing is set.
        """
        path = f'/apps/{_q(app_id)}/deployments/current'
        return self._c._r('GET', path) or t.DeployCurrent()


class AsyncDeploys(_AsyncGroup):
    """The async version of :class:`Deploys`, reached as ``client.apps.deploys``."""

    set_webhook = _aio(Deploys.set_webhook)
    link_github_app = _aio(Deploys.link_github_app)
    unlink_github_app = _aio(Deploys.unlink_github_app)
    list = _aio(Deploys.list)
    current = _aio(Deploys.current)


class Envs(_Group):
    """Read and change an application's environment variables.

    Reach it as ``client.apps.envs``. Each ``app_id`` accepts the same ids
    as :class:`Apps`, including the composite id of a workspace application. The
    variables are a ``dict`` of names to string values, at most 256 of them.
    A change while another one is in progress fails with 409 ``ENV_BUSY``,
    so try again. Static applications have no environment variables, so
    every method fails for them with 400 ``STATIC_APP_ENV_NOT_SUPPORTED``.
    """

    def get(self, app_id: str) -> t.EnvVars:
        """Return the application's environment variables.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
        """
        return self._c._r('GET', f'/apps/{_q(app_id)}/envs')

    def set(self, app_id: str, envs: t.EnvVars) -> t.EnvVars:
        """Add or update the given variables and keep the others.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            envs: The variables to add or update.

        Returns:
            All of the application's variables after the change. An API key
            without the ``envs:read`` scope gets back only the variables it
            sent.

        Raises:
            SquareCloudAPIError: 400 ``TOO_MANY_ENV_VARS`` when the
                application would have more than 256 variables.
        """
        return self._c._r('POST', f'/apps/{_q(app_id)}/envs', json_body={'envs': envs})

    def replace(self, app_id: str, envs: t.EnvVars) -> t.EnvVars:
        """Replace all of the application's variables with ``envs``.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            envs: The new variables. Pass ``{}`` to remove every variable.

        Returns:
            The application's variables after the change.

        Raises:
            SquareCloudAPIError: 400 ``TOO_MANY_ENV_VARS`` when ``envs`` has
                more than 256 variables.
        """
        return self._c._r('PUT', f'/apps/{_q(app_id)}/envs', json_body={'envs': envs})

    def delete(self, app_id: str, keys: str | Iterable[str]) -> t.EnvVars:
        """Remove one variable or several.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            keys: One name, or an iterable of names. Names that do not exist
                are ignored.

        Returns:
            The variables that remain. An API key without the ``envs:read``
            scope gets ``{}``.
        """
        names = [keys] if isinstance(keys, str) else list(keys)
        return self._c._r(
            'DELETE', f'/apps/{_q(app_id)}/envs', json_body={'envs': names}
        )


class AsyncEnvs(_AsyncGroup):
    """The async version of :class:`Envs`, reached as ``client.apps.envs``."""

    get = _aio(Envs.get)
    set = _aio(Envs.set)
    replace = _aio(Envs.replace)
    delete = _aio(Envs.delete)


class Files(_Group):
    """Read and change the files of an application.

    Reach it as ``client.apps.files``. Each ``app_id`` accepts the same ids
    as :class:`Apps`, including the composite id of a workspace application. Paths
    are at most 256 characters.
    """

    def list(self, app_id: str, path: str | None = None) -> builtins.list[t.FileEntry]:
        """List the files and directories in a directory.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            path: The directory to list. Defaults to the application root.

        Returns:
            The entries, each with its ``name`` and its ``type``, which is
            ``'file'`` or ``'directory'``.

        Raises:
            SquareCloudAPIError: 404 ``FILE_NOT_FOUND`` when the directory
                does not exist. 403 ``BLOCKED_PATH`` when it is protected.
        """
        return self._c._r('GET', f'/apps/{_q(app_id)}/files', query={'path': path})

    def read(self, app_id: str, path: str) -> bytes:
        """Return the contents of a file.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            path: The file to read.

        Returns:
            The file's bytes.

        Raises:
            SquareCloudAPIError: 404 ``FILE_NOT_FOUND`` when the file does
                not exist. 413 ``FILE_TOO_LARGE`` when it is over 10 MB.
        """
        r = self._c._r(
            'GET',
            f'/apps/{_q(app_id)}/files/content',
            query={'path': path, 'encoding': 'base64'},
        )
        return base64.b64decode((r or {}).get('data') or '')

    def write(self, app_id: str, path: str, content: str | bytes) -> None:
        """Create or overwrite a file.

        A ``str`` is sent as text. ``bytes`` are sent base64-encoded, so
        binary content arrives unchanged. Empty content creates an empty
        file. Content over 1 MiB is sent without a timeout, like an upload.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            path: The file to write.
            content: The new contents, at most 10 MB.

        Raises:
            SquareCloudAPIError: ``FILE_TOO_LARGE`` with status 0 when the
                content is over 10 MB, in which case nothing is sent. Use
                :meth:`Apps.commit` for larger files.
        """
        endpoint = f'/apps/{_q(app_id)}/files'
        # Every character takes at least one byte, so text that is too long
        # is rejected before it is encoded.
        too_large = len(content) > MAX_FILE_BYTES
        if not too_large:
            data = content.encode() if isinstance(content, str) else bytes(content)
            too_large = len(data) > MAX_FILE_BYTES
        if too_large:
            raise _too_large(
                'The content is larger than the 10 MB file write limit, so it was '
                'not sent. Upload larger files with apps.commit().',
                'PUT',
                self._c._base_path + endpoint,
            )
        body = (
            {'path': path, 'content': content}
            if isinstance(content, str)
            else {
                'path': path,
                'content': base64.b64encode(data).decode(),
                'encoding': 'base64',
            }
        )
        self._c._request(
            'PUT',
            endpoint,
            json_body=body,
            no_timeout=len(data) > _NO_TIMEOUT_BYTES,  # Sent like an upload.
        )

    def move(self, app_id: str, path: str, to: str) -> None:
        """Move or rename a file.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            path: The current path.
            to: The new path.
        """
        self._c._request(
            'PATCH',
            f'/apps/{_q(app_id)}/files',
            json_body={'path': path, 'to': to},
        )

    def delete(self, app_id: str, path: str) -> None:
        """Delete a file.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            path: The file to delete.
        """
        self._c._request(
            'DELETE', f'/apps/{_q(app_id)}/files', json_body={'path': path}
        )


class AsyncFiles(_AsyncGroup):
    """The async version of :class:`Files`, reached as ``client.apps.files``."""

    list = _aio(Files.list)
    read = _aio(Files.read)
    write = _aio(Files.write)
    move = _aio(Files.move)
    delete = _aio(Files.delete)


class Network(_Group):
    """Inspect the traffic of a website and manage its custom domain.

    Reach it as ``client.apps.network``. Each ``app_id`` accepts the same
    ids as :class:`Apps`, including the composite id of a workspace application.

    ``start`` and ``end`` take an ISO 8601 string, which is sent as is, or a
    ``datetime``, which is sent in UTC. A naive ``datetime`` is read as
    local time. The data reaches back at most 7 days. :meth:`analytics`,
    :meth:`errors`, :meth:`logs` and :meth:`performance` share a limit of
    20 calls a minute for data that is not cached, and past it they fail
    with 429 ``RATE_LIMITED``.
    """

    def analytics(
        self,
        app_id: str,
        start: Time,
        end: Time,
        **filters: Unpack[t.AnalyticsFilters],
    ) -> t.NetworkAnalytics | None:
        """Return the traffic of the application's domains between two times.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            start: The start of the window.
            end: The end of the window.
            **filters: Optional filters, passed as keywords, such as
                ``country='BR'``, ``status='404'`` or ``path='/api'``.
                ``provider`` takes the ``'NAME (ASN)'`` form that the
                ``providers`` buckets report, such as
                ``'GOOGLE (15169)'``. See
                :class:`~squarecloud.types.AnalyticsFilters` for all of
                them.

        Returns:
            The traffic broken down by country, path, status and more, or
            ``None`` when the window has no traffic.

        Raises:
            SquareCloudAPIError: 400 ``INVALID_FILTER`` for a filter the API
                does not accept.
        """
        query = {'start': _iso(start), 'end': _iso(end), **filters}
        endpoint = f'/apps/{_q(app_id)}/network/analytics'
        return self._c._r('GET', endpoint, query=query) or None

    def errors(
        self, app_id: str, start: Time, end: Time, *, include_4xx: bool = False
    ) -> t.NetworkErrors | None:
        """Return the HTTP errors served on the application's domains.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            start: The start of the window.
            end: The end of the window.
            include_4xx: Count 4xx responses too. By default only 5xx
                responses are counted.

        Returns:
            The errors by status, path, method and time, or ``None`` when
            the window has no traffic.
        """
        query = {
            'start': _iso(start),
            'end': _iso(end),
            'include_4xx': 'true' if include_4xx else None,
        }
        endpoint = f'/apps/{_q(app_id)}/network/errors'
        return self._c._r('GET', endpoint, query=query) or None

    def logs(self, app_id: str, start: Time, end: Time) -> list[t.NetworkLog]:
        """Return the requests served on the application's domains.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            start: The start of the window.
            end: The end of the window.

        Raises:
            SquareCloudAPIError: 403 ``UPGRADE_REQUIRED`` on plans other
                than Pro and Enterprise.
        """
        return self._c._r(
            'GET',
            f'/apps/{_q(app_id)}/network/logs',
            query={'start': _iso(start), 'end': _iso(end)},
        )

    def performance(
        self, app_id: str, start: Time, end: Time
    ) -> t.NetworkPerformance | None:
        """Return the response times of the application's domains.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            start: The start of the window.
            end: The end of the window.

        Returns:
            Latency percentiles overall, by country and for the slowest
            paths, or ``None`` when the window has no traffic.

        Raises:
            SquareCloudAPIError: 403 ``UPGRADE_REQUIRED`` on plans other
                than Pro and Enterprise.
        """
        return (
            self._c._r(
                'GET',
                f'/apps/{_q(app_id)}/network/performance',
                query={'start': _iso(start), 'end': _iso(end)},
            )
            or None
        )

    def dns(self, app_id: str) -> list[t.DNSRecord]:
        """Return the DNS records to create for the application's custom domain.

        Each record's ``status`` shows whether it is validated yet, and its
        ``errors`` explain why not.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).

        Raises:
            SquareCloudAPIError: 400 ``NO_CUSTOM_DOMAIN`` when the
                application has no custom domain.
        """
        return self._c._r('GET', f'/apps/{_q(app_id)}/network/dns')

    def set_domain(self, app_id: str, domain: str) -> None:
        """Set or remove the custom domain of a website.

        Then create the records that :meth:`dns` returns.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
            domain: A fully qualified domain name, such as
                ``'www.example.com'``. Pass ``'@'`` to remove the current
                one.

        Raises:
            SquareCloudAPIError: 403 ``UPGRADE_REQUIRED`` on plans other
                than Standard, Pro and Enterprise. 400 ``RESERVED_DOMAIN``
                for a Square Cloud domain. 409 ``DOMAIN_ALREADY_EXISTS``
                when another account uses the domain. 403
                ``LOAD_BALANCER_LIMIT_REACHED`` when the domain is already
                on as many of your applications as your plan allows.
        """
        self._c._request(
            'POST',
            f'/apps/{_q(app_id)}/network/custom',
            json_body={'custom': domain},
        )

    def purge_cache(self, app_id: str) -> None:
        """Clear the cached responses of the application's domains.

        Args:
            app_id: The application id (see :class:`Apps` for workspace apps).
        """
        self._c._request('POST', f'/apps/{_q(app_id)}/network/purge_cache')


class AsyncNetwork(_AsyncGroup):
    """The async version of :class:`Network`, reached as ``client.apps.network``."""

    analytics = _aio(Network.analytics)
    errors = _aio(Network.errors)
    logs = _aio(Network.logs)
    performance = _aio(Network.performance)
    dns = _aio(Network.dns)
    set_domain = _aio(Network.set_domain)
    purge_cache = _aio(Network.purge_cache)
