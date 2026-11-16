"""The ``databases`` group. Its ``snapshots`` group lives in :mod:`.snapshots`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from .. import types as t
from .._group import _aio, _AsyncGroup, _Group
from .._wire import _SLOW, _q
from .snapshots import AsyncSnapshots, Snapshots

if TYPE_CHECKING:
    from ..client import SquareCloud


class Databases(_Group):
    """Create, control and inspect your databases.

    Reach it as ``client.databases``. Its nested group ``snapshots`` takes
    and restores database snapshots. Every ``database_id`` is the id that
    :meth:`create` returns.
    """

    def __init__(self, client: SquareCloud) -> None:
        super().__init__(client)
        self.snapshots = Snapshots(client, '/databases')

    def create(
        self, name: str, *, type: t.DatabaseType, version: str, memory: int
    ) -> t.DatabaseCreated:
        """Create a database.

        The call waits at least 120 seconds for the answer, even when the
        client's ``timeout`` is shorter.

        Args:
            name: The display name.
            type: The engine, which is ``'mongo'``, ``'mysql'``, ``'redis'``
                or ``'postgres'``.
            version: The engine version. A major version such as ``'8'``
                works.
            memory: The memory to allocate, as an ``int`` in MB. A float or
                a string fails with 400 ``INVALID_MEMORY``.

        Returns:
            The new database, with its ``password``, ``connection_url`` and
            TLS ``certificate``. Store the password now, because the API
            returns it only once. :meth:`reset_credentials` sets a new one.

        Raises:
            SquareCloudAPIError: 403 ``UPGRADE_REQUIRED`` on plans other
                than Standard, Pro and Enterprise. 400
                ``INSUFFICIENT_MEMORY`` when your plan does not have enough
                free memory.
        """
        return self._c._r(
            'POST',
            '/databases',
            json_body={
                'name': name,
                'type': type,
                'version': version,
                'memory': memory,
            },
            min_timeout=_SLOW,
        )

    def get(self, database_id: str) -> t.Database:
        """Return the database's name, owner, engine, memory and port.

        Args:
            database_id: The database id.
        """
        return self._c._r('GET', f'/databases/{_q(database_id)}')

    def update(
        self,
        database_id: str,
        *,
        name: str | None = None,
        ram: int | None = None,
    ) -> None:
        """Rename the database or change its memory.

        Pass at least one of ``name`` and ``ram``.

        Args:
            database_id: The database id.
            name: The new display name.
            ram: The new memory, as an ``int`` in MB.
        """
        body = {'name': name, 'ram': ram}
        self._c._request(
            'PATCH',
            f'/databases/{_q(database_id)}',
            json_body={k: v for k, v in body.items() if v is not None},
        )

    def delete(self, database_id: str) -> None:
        """Delete the database.

        Args:
            database_id: The database id.

        Raises:
            SquareCloudAPIError: 409 ``RESTORE_IN_PROGRESS`` while a
                snapshot restore is running. Try again when it ends.
        """
        self._c._request('DELETE', f'/databases/{_q(database_id)}')

    def start(self, database_id: str) -> None:
        """Start the database.

        The call waits at least 120 seconds for the answer, even when the
        client's ``timeout`` is shorter.

        Args:
            database_id: The database id.

        Raises:
            SquareCloudAPIError: A refused start is a 409 whose ``code`` is
                ``CONTAINER_ALREADY_STARTED``, ``CONTAINER_ALREADY_STOPPED``,
                ``CONTAINER_NOT_FOUND``, ``CONTAINER_INSUFFICIENT_DISK_SPACE``,
                ``CONTAINER_NETWORK_CONFLICT``, ``ACTION_FAILED`` or
                ``RESTORE_IN_PROGRESS``. After ``RESTORE_IN_PROGRESS``, try
                again when the restore ends.
        """
        self._c._request(
            'POST', f'/databases/{_q(database_id)}/start', min_timeout=_SLOW
        )

    def stop(self, database_id: str) -> None:
        """Stop the database.

        The call waits at least 120 seconds for the answer, even when the
        client's ``timeout`` is shorter.

        Args:
            database_id: The database id.

        Raises:
            SquareCloudAPIError: A refused stop is a 409 with the same codes
                as :meth:`start`, such as ``CONTAINER_ALREADY_STOPPED``.
        """
        self._c._request(
            'POST', f'/databases/{_q(database_id)}/stop', min_timeout=_SLOW
        )

    def status(self, database_id: str, *, raw: bool = False) -> t.RuntimeStats:
        """Return the database's current CPU, memory, network and storage usage.

        Args:
            database_id: The database id.
            raw: Return numbers instead of formatted strings such as
                ``'120.4MB'``. CPU is then a percentage, memory is in MB, and
                storage and network are in bytes.
        """
        return self._c._r(
            'GET',
            f'/databases/{_q(database_id)}/status',
            query={'rawData': 'true' if raw else None},
        )

    def metrics(
        self, database_id: str, *, range: Literal['24h', '7d'] | None = None
    ) -> list[t.MetricPoint]:
        """Return the database's usage history, newest point first.

        Args:
            database_id: The database id.
            range: ``'24h'``, the default, returns one point every 5
                minutes. ``'7d'`` returns hourly points with the hour's
                peaks in ``cpu_max`` and ``ram_max``. It needs a Pro or
                Enterprise plan. Otherwise the API returns the 24-hour
                history without an error.

        Raises:
            SquareCloudAPIError: 400 ``INVALID_PARAMETERS`` for any other
                ``range``.
        """
        return self._c._r(
            'GET', f'/databases/{_q(database_id)}/metrics', query={'range': range}
        )

    def status_all(self) -> list[t.StatusListItem]:
        """Return whether each of your databases is running, and its usage.

        Stopped databases are included, without ``cpu`` and ``ram``.
        """
        return self._c._r('GET', '/databases/status')

    def certificate(self, database_id: str) -> str:
        """Return the database's TLS certificate, base64-encoded.

        ``base64.b64decode`` turns it into a PEM file that holds the private
        key followed by the certificate. The database must be running.

        Args:
            database_id: The database id.
        """
        r = self._c._r('GET', f'/databases/{_q(database_id)}/credentials/certificate')
        return str((r or {}).get('certificate') or '')

    def reset_credentials(
        self, database_id: str, reset: Literal['password', 'certificate']
    ) -> str:
        """Replace the database's password or TLS certificate.

        The database must be running.

        Args:
            database_id: The database id.
            reset: ``'password'`` or ``'certificate'``.

        Returns:
            The new password, or ``''`` after a certificate reset. Fetch the
            new certificate with :meth:`certificate`.
        """
        r = self._c._r(
            'POST',
            f'/databases/{_q(database_id)}/credentials/reset',
            json_body={'reset': reset},
        )
        return str((r or {}).get('password') or '')


class AsyncDatabases(_AsyncGroup):
    """The async version of :class:`Databases`, reached as ``client.databases``.

    Every method takes the same arguments as in :class:`Databases` and
    returns a coroutine.
    """

    def __init__(self, sync: Databases) -> None:
        super().__init__(sync)
        self.snapshots = AsyncSnapshots(sync.snapshots)

    create = _aio(Databases.create)
    get = _aio(Databases.get)
    update = _aio(Databases.update)
    delete = _aio(Databases.delete)
    start = _aio(Databases.start)
    stop = _aio(Databases.stop)
    status = _aio(Databases.status)
    metrics = _aio(Databases.metrics)
    status_all = _aio(Databases.status_all)
    certificate = _aio(Databases.certificate)
    reset_credentials = _aio(Databases.reset_credentials)
