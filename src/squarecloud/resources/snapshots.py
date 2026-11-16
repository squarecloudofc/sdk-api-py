"""The ``snapshots`` group, shared by ``apps`` and ``databases``."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, cast

from .. import types as t
from .._group import _aio, _AsyncGroup, _Group
from .._wire import _SLOW, _q

if TYPE_CHECKING:
    from ..client import SquareCloud


class Snapshots(_Group):
    """Take, list and restore snapshots of an application or a database.

    Reach it as ``client.apps.snapshots`` or ``client.databases.snapshots``.
    On ``apps``, ``resource_id`` accepts the same ids as
    :class:`~squarecloud.resources.apps.Apps`, including the composite id of
    a workspace application. On ``databases``, it is the database id.
    """

    def __init__(self, client: SquareCloud, prefix: str) -> None:
        super().__init__(client)
        self._prefix = prefix

    def list(self, resource_id: str) -> builtins.list[t.Snapshot]:
        """Return the stored snapshots.

        Args:
            resource_id: The application id or the database id (see
                :class:`Snapshots`).

        Returns:
            The snapshots. Each one carries the ``name`` and ``version_id``
            that :meth:`restore` needs, and a signed download ``url`` that
            is valid for 1 hour.

        Raises:
            SquareCloudAPIError: 503 ``SNAPSHOTS_UNAVAILABLE`` when snapshot
                storage cannot answer. Try again in about 30 seconds.
        """
        return self._c._r('GET', f'{self._prefix}/{_q(resource_id)}/snapshots')

    def create(self, resource_id: str) -> t.SnapshotCreated:
        """Take a snapshot now.

        The call waits at least 120 seconds for the answer. A snapshot that
        is not ready after about 90 seconds keeps being generated, and the
        call returns ``{'pending': True}``. The snapshot
        then shows up in :meth:`list` on its own, usually within 2 minutes.
        Poll :meth:`list` instead of calling ``create`` again, which allows
        one call every 180 seconds and counts against your plan's daily
        snapshot quota.

        Args:
            resource_id: The application id or the database id (see
                :class:`Snapshots`).

        Returns:
            ``{'pending': False, 'url': ..., 'key': ...}`` when the snapshot
            is ready, or ``{'pending': True}`` while it is still being
            generated. The ``url`` is a download link that is valid for 1
            hour (see ``client.download_snapshot``). An API key without the
            ``snapshots:read`` scope gets ``''`` for ``url`` and ``key``.

        Raises:
            SquareCloudAPIError: 409 ``RESTORE_IN_PROGRESS`` while a
                snapshot restore is running, so try again when it ends. 429
                ``DAILY_SNAPSHOTS_LIMIT_REACHED`` when your plan's daily
                quota is used up. 503 ``CLUSTER_MAINTENANCE_TRY_LATER``
                during maintenance, so try again in a few minutes.
        """
        r = self._c._request(
            'POST',
            f'{self._prefix}/{_q(resource_id)}/snapshots',
            min_timeout=_SLOW,
            pending=True,
        )
        if r['pending']:
            return {'pending': True}
        # Without snapshots:read, the API leaves out both or sends null.
        r.update(url=r.get('url') or '', key=r.get('key') or '')
        return cast(t.SnapshotCreated, r)

    def restore(
        self, resource_id: str, name: str, version_id: str
    ) -> t.SnapshotRestored:
        """Restore a snapshot, replacing the current contents.

        The call waits at least 120 seconds for the answer. A restore that
        is not done after about 90 seconds keeps running, and the call
        returns ``{'pending': True}``. Follow it with
        :meth:`restore_state` and do not call ``restore`` again.

        Args:
            resource_id: The application id or the database id (see
                :class:`Snapshots`).
            name: The snapshot's ``name``, from :meth:`list`.
            version_id: The snapshot's ``version_id``, from :meth:`list`.

        Returns:
            ``{'pending': False}`` when the restore is done, or
            ``{'pending': True}`` while it is still running.

        Raises:
            SquareCloudAPIError: 400 ``MISSING_PARAMETERS``,
                ``INVALID_SNAPSHOT_ID`` or ``INVALID_VERSION_ID`` for a bad
                ``name`` or ``version_id``. A database also fails with
                ``SNAPSHOT_DATABASE_MISMATCH`` for a snapshot of another
                engine. 404 ``APP_NOT_FOUND``, ``DATABASE_NOT_FOUND``,
                ``SNAPSHOT_NOT_FOUND``, ``SNAPSHOT_RESTORE_FAILED``,
                ``SNAPSHOT_CORRUPT``, ``RESTORE_INTERRUPTED`` or
                ``CONTAINER_NOT_FOUND``. 409 ``RESTORE_IN_PROGRESS`` or
                ``SNAPSHOT_IN_PROGRESS`` while another restore or snapshot
                is running. 413 ``PAYLOAD_TOO_LARGE``. 503
                ``CLUSTER_MAINTENANCE_TRY_LATER`` during maintenance.
        """
        r = self._c._request(
            'POST',
            f'{self._prefix}/{_q(resource_id)}/snapshots/restore',
            json_body={'snapshotId': name, 'versionId': version_id},
            min_timeout=_SLOW,
            pending=True,
        )
        return {'pending': r['pending']}

    def restore_state(self, resource_id: str) -> t.SnapshotRestoreState:
        """Return the progress or outcome of the last snapshot restore.

        ``state`` is ``'queued'`` or ``'running'`` while the restore runs,
        with the current ``step``. It is then ``'success'``, or ``'error'``
        with a ``code``, for 1 hour after the restore ends, and ``'none'``
        when there is no recent restore. It allows up to 30 calls a minute,
        so poll it every few seconds.

        Args:
            resource_id: The application id or the database id (see
                :class:`Snapshots`).
        """
        return self._c._r('GET', f'{self._prefix}/{_q(resource_id)}/snapshots/restore')


class AsyncSnapshots(_AsyncGroup):
    """The async version of :class:`Snapshots`."""

    list = _aio(Snapshots.list)
    create = _aio(Snapshots.create)
    restore = _aio(Snapshots.restore)
    restore_state = _aio(Snapshots.restore_state)
