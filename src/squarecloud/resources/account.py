"""The ``account``, ``service`` and ``ai`` groups."""

from __future__ import annotations

from typing import Any

from .. import types as t
from .._group import _aio, _AsyncGroup, _Group
from .._wire import _AI


class Account(_Group):
    """Read your profile and your snapshots.

    Reach it as ``client.account``.
    """

    def me(self) -> t.Account:
        """Return your profile, plan, applications and databases.

        An API key limited to specific resources sees only those
        applications and databases.
        """
        return self._c._r('GET', '/users/me')

    def snapshots(self, *, scope: t.SnapshotScope | None = None) -> list[t.Snapshot]:
        """Return the snapshots of all your applications or all your databases.

        Args:
            scope: ``'applications'``, the default, or ``'databases'``.

        Returns:
            The snapshots. Each one carries the ``version_id`` that a
            restore needs and a signed download ``url`` that is valid for 1
            hour.

        Raises:
            SquareCloudAPIError: 402 ``UPGRADE_REQUIRED`` when the account
                has no active paid plan. 429 ``RATE_LIMITED`` after 3 calls
                in a minute. 503 ``SNAPSHOTS_UNAVAILABLE`` when snapshot
                storage cannot answer, so try again in about 30 seconds.
        """
        return self._c._r('GET', '/users/snapshots', query={'scope': scope})


class AsyncAccount(_AsyncGroup):
    """The async version of :class:`Account`, reached as ``client.account``."""

    me = _aio(Account.me)
    snapshots = _aio(Account.snapshots)


class Service(_Group):
    """Check the status of Square Cloud.

    Reach it as ``client.service``.
    """

    def status(self) -> t.ServiceStatus:
        """Return the status of Square Cloud and of the services it depends on.

        The API does not check the API key on this call, but the client
        still needs a non-empty key to be created.
        """
        return self._c._request('GET', '/service/status', raw=True)


class AsyncService(_AsyncGroup):
    """The async version of :class:`Service`, reached as ``client.service``."""

    status = _aio(Service.status)


class AI(_Group):
    """Chat with Square Cloud AI through an OpenAI-compatible API.

    Reach it as ``client.ai``.
    """

    def chat(self, request: t.ChatRequest | dict[str, Any]) -> t.ChatCompletion:
        """Send a chat completion request and return the model's reply.

        The request is sent as given, so any OpenAI chat parameter works.
        Streaming is not supported. It needs a Standard, Pro or Enterprise
        plan and an API key with the ``ai:chat`` scope. The API answers
        within 90 seconds, and the call waits at least 120 seconds for it.

        Args:
            request: The request body, with ``messages`` and optionally
                ``model`` and other OpenAI parameters.

        Returns:
            The completion, in the OpenAI format.

        Raises:
            SquareCloudAPIError: Errors on this call carry the lowercase
                codes of the OpenAI format, such as ``access_denied``, 403
                ``upgrade_required`` on a plan without AI,
                ``rate_limit_exceeded``, ``weekly_limit_reached`` or
                ``server_overloaded``. A 503 ``server_overloaded`` means the
                request ran past the 90-second limit. It is safe to send
                again, but the SDK does not retry it for you.
        """
        return self._c._request(
            'POST', '/ai/chat/completions', json_body=request, raw=True, min_timeout=_AI
        )


class AsyncAI(_AsyncGroup):
    """The async version of :class:`AI`, reached as ``client.ai``."""

    chat = _aio(AI.chat)
