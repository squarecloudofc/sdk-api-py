from __future__ import annotations


class SquareCloudAPIError(Exception):
    """The only exception the SDK raises for API and network failures.

    ``status`` is the HTTP status (``0`` for network errors and timeouts).
    ``code`` is the API's error code (``'APP_NOT_FOUND'``, ``'MISSING_SCOPE'``,
    ``'RATE_LIMITED'``...) or one of the SDK codes ``'NETWORK_ERROR'``,
    ``'TIMEOUT'``, ``'FILE_TOO_LARGE'``, ``'INVALID_ID'`` (the last two are
    local checks, status ``0``) and ``'UNKNOWN_ERROR'`` (no code in the
    body). ``method`` and ``path`` (e.g. ``'/v2/apps/<id>'``) name the call.

    429 ``'RATE_LIMITED'`` is the account/API-key/IP block (it can last
    ~30 min) and the limit of the app network endpoints and of
    ``GET /v2/users/snapshots``; ``'KEEP_CALM'`` is a route's own limit.
    ``'RATE_LIMIT'`` and ``'RATE_LIMIT_EXCEEDED'`` are their deprecated
    names. A 429 is never retried. 401 ``'ACCESS_DENIED'`` is an unknown,
    revoked or expired key. Start/stop/restart refusals are 409
    ``'CONTAINER_ALREADY_STARTED'``, ``'CONTAINER_ALREADY_STOPPED'``,
    ``'CONTAINER_TEMPORARILY_SUSPENDED'`` (apps only),
    ``'CONTAINER_NOT_FOUND'``, ``'CONTAINER_INSUFFICIENT_DISK_SPACE'``,
    ``'CONTAINER_NETWORK_CONFLICT'`` or ``'ACTION_FAILED'``, with no
    message (``message`` is ``''``). 503 ``'DATABASE_UNAVAILABLE'`` is
    retried on GET only: it can fire after a mutation was applied, so
    retrying an idempotent mutation (a ``PUT``, a ``stop``) is up to the
    caller. The AI route (``ai.chat``) reports every error, auth, 429 and
    503 included, with the OpenAI error's lowercase code
    (``'access_denied'``, ``'rate_limit_exceeded'``, ``'server_overloaded'``).
    ``cause`` is the original exception of a network error or of a 2xx body
    that is not JSON (``None`` otherwise). ``str(e)`` is
    ``'<METHOD> <path>: HTTP <status> <CODE>: <message>'``, without
    ``HTTP <status>`` when the status is ``0`` and without ``: <message>``
    when it is empty.

    Local file errors (a missing upload path, a file unreadable mid-upload,
    an unwritable download destination) propagate as ``OSError``.

    Known API codes (the list grows: treat an unknown code as a generic
    failure of its HTTP status; ``RATE_LIMIT`` and ``RATE_LIMIT_EXCEEDED``
    are deprecated):
    ACCESS_DENIED, ACTION_FAILED, AI_DAILY_LIMIT_REACHED,
    AI_MAX_CONCURRENT_STREAMS, AI_NO_PLAN_LIMIT_REACHED, AI_UNAVAILABLE,
    ANALYTICS_BUSY, APPLICATIONS_LIMIT_REACHED, APP_ALREADY_IN_WORKSPACE,
    APP_NOT_FOUND, BLOCKED_PATH, BRANCH_NOT_FOUND, CANNOT_EDIT_OWNER,
    CANNOT_INVITE_OWNER, CANNOT_LEAVE_OWNER, CANNOT_SET_SUBDOMAIN,
    CLUSTER_MAINTENANCE_TRY_LATER, CLUSTER_SELECTION_FAILED,
    CLUSTER_TIMEOUT, CLUSTER_UNAVAILABLE, COMMIT_FAILED,
    CONFLICTING_RESOURCES, CONTAINER_ALREADY_STARTED,
    CONTAINER_ALREADY_STOPPED, CONTAINER_INSUFFICIENT_DISK_SPACE,
    CONTAINER_NETWORK_CONFLICT, CONTAINER_NOT_FOUND,
    CONTAINER_TEMPORARILY_SUSPENDED, DAILY_SNAPSHOTS_LIMIT_REACHED,
    DATABASE_CREATION_FAILED, DATABASE_NOT_FOUND, DATABASE_NOT_RUNNING,
    DATABASE_UNAVAILABLE, DELETE_FAILED, DNS_FAILED,
    DOMAIN_ALREADY_EXISTS, EMPTY_RESPONSE, ENV_CONTENT_TOO_LONG,
    ENV_NAME_TOO_LONG, FAILED_TO_FETCH, FILE_NOT_FOUND, FILE_TOO_LARGE,
    GITHUB_NOT_CONNECTED, GIT_ALREADY_CONFIGURED, GIT_NOT_CONFIGURED,
    INSUFFICIENT_MEMORY, INTERNAL_SERVER_ERROR, INVALID_ACCESS_TOKEN,
    INVALID_AUTORESTART, INVALID_BRANCH_LENGTH, INVALID_CODE,
    INVALID_CONTENT, INVALID_CONTENT_TYPE, INVALID_DATABASE_TYPE,
    INVALID_DATABASE_VERSION, INVALID_DESCRIPTION, INVALID_DISPLAY_NAME,
    INVALID_DOMAIN, INVALID_ENCODING, INVALID_ENV_CONTENT, INVALID_FILE,
    INVALID_FILENAME, INVALID_FILTER, INVALID_GROUP, INVALID_ID,
    INVALID_INPUT, INVALID_JSON_BODY, INVALID_MEMORY, INVALID_NAME,
    INVALID_PARAMETERS, INVALID_PATH, INVALID_RESET_TYPE, INVALID_SCOPE,
    INVALID_SNAPSHOT_ID, INVALID_SUBDOMAIN, INVALID_TIME_RANGE,
    INVALID_VERSION_ID, KEEP_CALM, LOAD_BALANCER_LIMIT_REACHED,
    LOGS_UNAVAILABLE, MEMBERS_LIMIT_REACHED, MEMBER_ALREADY_ADDED,
    MEMBER_NOT_FOUND, METRICS_NOT_SUPPORTED, MISSING_PARAMETERS,
    MISSING_REQUIRED_FIELDS, MISSING_SCOPE, NO_CUSTOM_DOMAIN,
    NO_UPDATE_DATA, PAYLOAD_TOO_LARGE, PERMISSION_DENIED,
    PURGE_CACHE_FAILED, RATE_LIMIT, RATE_LIMITED, RATE_LIMIT_EXCEEDED,
    READ_FAILED, REALTIME_MAX_CONNECTIONS, REALTIME_MAX_CONNECTIONS_APP,
    RENAME_FAILED, REPOSITORY_BRANCH_ALREADY_CONFIGURED,
    REPOSITORY_NOT_AVAILABLE, REPOSITORY_NOT_FOUND,
    REPOSITORY_PERMISSION_REQUIRED, REQUEST_ABORTED, RESERVED_DOMAIN,
    RESET_FAILED, RESOURCE_NOT_ALLOWED, RESTORE_IN_PROGRESS,
    ROUTE_NOT_FOUND, SAVE_FAILED, SCOPE_NOT_GRANTABLE,
    SNAPSHOT_DATABASE_MISMATCH, SNAPSHOT_FAILED, SNAPSHOT_NOT_FOUND,
    SNAPSHOT_PROCESSING, SNAPSHOT_RESTORE_FAILED,
    STATIC_APP_ENV_NOT_SUPPORTED, STORAGE_UPLOAD_FAILED,
    TOO_MANY_ENV_VARS, UNABLE_TO_FETCH_ANALYTICS, UNABLE_TO_FETCH_ERRORS,
    UNABLE_TO_FETCH_PERFORMANCE, UPGRADE_REQUIRED, UPLOAD_ABORTED,
    UPLOAD_BUSY, UPLOAD_FAILED, VALIDATION_FAILED,
    VALIDATION_TIMEOUT, WORKSPACE_CREATION_FAILED, WORKSPACE_LIMIT_REACHED,
    WORKSPACE_NOT_FOUND.
    """

    def __init__(
        self,
        status: int,
        code: str,
        message: str = '',
        method: str = '',
        path: str = '',
    ) -> None:
        super().__init__(status, code, message, method, path)
        self.status = status
        self.code = code
        self.message = message
        self.method = method
        self.path = path

    @property
    def cause(self) -> BaseException | None:
        return self.__cause__

    def __str__(self) -> str:
        text = f'HTTP {self.status} {self.code}' if self.status else self.code
        if self.method:
            text = f'{self.method} {self.path}: {text}'
        return f'{text}: {self.message}' if self.message else text
