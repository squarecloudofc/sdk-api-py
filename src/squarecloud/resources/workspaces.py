"""The ``workspaces`` group and its nested ``members`` and ``apps`` groups."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from .. import types as t
from .._group import _aio, _AsyncGroup, _Group
from .._wire import _q

if TYPE_CHECKING:
    from ..client import SquareCloud


class Workspaces(_Group):
    """Create and manage workspaces, where you share applications with others.

    Reach it as ``client.workspaces``. Its nested groups are ``members`` and
    ``apps``. Members reach a shared application through the ``apps``
    group with the composite id ``'<appId>-<workspaceId>'``.
    """

    def __init__(self, client: SquareCloud) -> None:
        super().__init__(client)
        self.members = Members(client)
        self.apps = WorkspaceApps(client)

    def create(self, name: str) -> t.WorkspaceCreated:
        """Create a workspace that you own.

        Args:
            name: The name, 1 to 32 letters, digits, spaces, hyphens or
                underscores.

        Returns:
            The new workspace's ``id`` and ``name``.

        Raises:
            SquareCloudAPIError: 403 ``UPGRADE_REQUIRED`` on plans other
                than Standard, Pro and Enterprise. 400
                ``WORKSPACE_LIMIT_REACHED`` when you already own as many
                workspaces as your plan allows.
        """
        return self._c._r('POST', '/workspaces', json_body={'name': name})

    def list(self) -> builtins.list[t.Workspace]:
        """Return every workspace you own or belong to.

        Each workspace comes with its members and shared applications.
        """
        return self._c._r('GET', '/workspaces')

    def get(self, workspace_id: str) -> t.Workspace:
        """Return a workspace with its members and shared applications.

        Args:
            workspace_id: The id of a workspace you own or belong to.
        """
        return self._c._r('GET', f'/workspaces/{_q(workspace_id)}')

    def delete(self, workspace_id: str) -> None:
        """Delete a workspace.

        Only the workspace owner can delete it.

        Args:
            workspace_id: The workspace id.
        """
        self._c._request(
            'DELETE', '/workspaces', json_body={'workspaceId': workspace_id}
        )

    def leave(self, workspace_id: str) -> None:
        """Leave a workspace you belong to.

        The owner cannot leave. Delete the workspace instead.

        Args:
            workspace_id: The workspace id.
        """
        self._c._request(
            'DELETE', '/workspaces/leave', json_body={'workspaceId': workspace_id}
        )


class AsyncWorkspaces(_AsyncGroup):
    """The async version of :class:`Workspaces`, reached as ``client.workspaces``.

    Every method takes the same arguments as in :class:`Workspaces` and
    returns a coroutine.
    """

    def __init__(self, sync: Workspaces) -> None:
        super().__init__(sync)
        self.members = AsyncMembers(sync.members)
        self.apps = AsyncWorkspaceApps(sync.apps)

    create = _aio(Workspaces.create)
    list = _aio(Workspaces.list)
    get = _aio(Workspaces.get)
    delete = _aio(Workspaces.delete)
    leave = _aio(Workspaces.leave)


class Members(_Group):
    """Add, update and remove the members of a workspace.

    Reach it as ``client.workspaces.members``. A member's ``group`` is their
    role. ``'admin'`` can manage everything, ``'maintain'`` adds access to
    commits, files, DNS and the cache, ``'manager'`` can monitor and start
    or stop applications, and ``'view'`` can only read.
    """

    def add(self, workspace_id: str, code: str, group: t.WorkspaceGroup) -> None:
        """Add a user to the workspace with the invite code they gave you.

        Args:
            workspace_id: The workspace id.
            code: The invite code the user got from :meth:`invite_code`.
            group: The member's role.
        """
        self._c._request(
            'POST',
            '/workspaces/members',
            json_body={'workspaceId': workspace_id, 'code': code, 'group': group},
        )

    def update(
        self, workspace_id: str, member_id: str, group: t.WorkspaceGroup
    ) -> None:
        """Change a member's role.

        Args:
            workspace_id: The workspace id.
            member_id: The member's user id.
            group: The new role.
        """
        self._c._request(
            'PATCH',
            '/workspaces/members',
            json_body={
                'workspaceId': workspace_id,
                'memberId': member_id,
                'group': group,
            },
        )

    def remove(self, workspace_id: str, member_id: str) -> None:
        """Remove a member from the workspace.

        Only the workspace owner can do this.

        Args:
            workspace_id: The workspace id.
            member_id: The member's user id.
        """
        self._c._request(
            'DELETE',
            '/workspaces/members',
            json_body={'workspaceId': workspace_id, 'memberId': member_id},
        )

    def invite_code(self) -> str:
        """Return an invite code for your own account.

        Give it to a workspace owner, who adds you with :meth:`add`. The
        code expires after 5 minutes, and you can get a new one every 5
        minutes.
        """
        return str(
            (self._c._r('GET', '/workspaces/members/code') or {}).get('code') or ''
        )


class AsyncMembers(_AsyncGroup):
    """The async version of :class:`Members`."""

    add = _aio(Members.add)
    update = _aio(Members.update)
    remove = _aio(Members.remove)
    invite_code = _aio(Members.invite_code)


class WorkspaceApps(_Group):
    """Share your applications with a workspace.

    Reach it as ``client.workspaces.apps``.
    """

    def add(self, workspace_id: str, app_id: str) -> None:
        """Share one of your applications with a workspace you own.

        Members then reach it with the composite id
        ``'<appId>-<workspaceId>'``.

        Args:
            workspace_id: The workspace id.
            app_id: The id of an application you own.
        """
        self._c._request(
            'POST',
            '/workspaces/applications',
            json_body={'workspaceId': workspace_id, 'appId': app_id},
        )

    def remove(self, workspace_id: str, app_id: str) -> None:
        """Stop sharing an application with the workspace.

        Only the workspace owner can do this.

        Args:
            workspace_id: The workspace id.
            app_id: The id of the shared application.
        """
        self._c._request(
            'DELETE',
            '/workspaces/applications',
            json_body={'workspaceId': workspace_id, 'appId': app_id},
        )


class AsyncWorkspaceApps(_AsyncGroup):
    """The async version of :class:`WorkspaceApps`."""

    add = _aio(WorkspaceApps.add)
    remove = _aio(WorkspaceApps.remove)
