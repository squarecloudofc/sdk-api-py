"""The error that every failed Square Cloud API call raises."""

from __future__ import annotations


class SquareCloudAPIError(Exception):
    """Raised for a failed API call, a network failure or a failed local check.

    It is the only error type the SDK raises for these failures. Check
    ``status`` for the HTTP status and ``code`` for the reason::

        try:
            client.apps.start(app_id)
        except SquareCloudAPIError as e:
            if e.code != 'CONTAINER_ALREADY_STARTED':
                raise

    ``str(e)`` reads ``<METHOD> <path>: HTTP <status> <CODE>: <message>``.
    The ``HTTP <status>`` part is left out when ``status`` is 0, and the
    ``: <message>`` part when the message is empty. Problems with a local
    file, such as a missing upload path or a download destination you
    cannot write to, raise ``OSError`` instead.

    Attributes:
        status: The HTTP status, or 0 when no response arrived or a local
            check stopped the call before it was sent.
        code: The API's error code, such as ``'APP_NOT_FOUND'``, or one of
            the SDK codes described below.
        message: The server's explanation. It is ``''`` when the server
            sent only a code, as the start, stop and restart refusals do.
        method: The HTTP method of the failed call.
        path: The path of the failed call, such as ``'/v2/apps/<id>'``. It
            never includes the query string.
        cause: The original exception of a network error, or of a
            successful response whose body is not JSON. ``None`` otherwise.

    The SDK sets these codes itself:

    - ``NETWORK_ERROR``, with status 0, means that no complete response
      arrived, for example because of a DNS failure or a dropped
      connection.
    - ``TIMEOUT``, with status 0, means that a connect or read took longer
      than the client's ``timeout``. A timeout is never retried.
    - ``INVALID_ID``, with status 0, means that an id was empty, ``.`` or
      ``..``. Nothing was sent.
    - ``FILE_TOO_LARGE``, with status 0, means that an upload was over
      100 MB or file content was over 10 MB. Nothing was sent. The API
      uses the same code with status 413.
    - ``UNKNOWN_ERROR`` means an error response without a code, such as a
      proxy error page, or a successful response whose body is not JSON.

    Codes worth handling:

    - 401 ``ACCESS_DENIED`` means the API key is unknown, revoked or
      expired.
    - 403 ``MISSING_SCOPE`` or ``RESOURCE_NOT_ALLOWED`` means the API key
      lacks the scope, or is limited to other applications or databases.
    - 429 ``RATE_LIMITED`` means you went over your plan's request limit,
      or over the limit of the ``apps.network`` calls or of
      ``account.snapshots``. The block on your account, API key or IP can
      last about 30 minutes. 429 ``KEEP_CALM`` is the limit of a single
      call. ``RATE_LIMIT`` and ``RATE_LIMIT_EXCEEDED`` are older names of
      ``RATE_LIMITED``. The SDK never retries a 429.
    - 409 ``RESTORE_IN_PROGRESS`` means a snapshot restore is running on
      the application or database. Try again when it ends.
    - 409 ``ENV_BUSY`` means another write to the environment variables is
      in progress. Try again.
    - 503 ``SNAPSHOTS_UNAVAILABLE`` means snapshot storage cannot answer.
      Try again in about 30 seconds.
    - 503 ``CLUSTER_MAINTENANCE_TRY_LATER`` means maintenance is in
      progress. Try again in a few minutes.
    - 503 ``DATABASE_UNAVAILABLE`` means the API is briefly unavailable.
      The SDK retries it on ``GET`` only, because on other methods the
      change may already have been applied. Retrying those is up to you.

    ``ai.chat`` reports every error with the lowercase code of the OpenAI
    format, such as ``access_denied``, ``rate_limit_exceeded``,
    ``weekly_limit_reached`` or ``server_overloaded``.

    The API can add codes, so treat an unknown code as a generic failure of
    its HTTP status. ``RATE_LIMIT``, ``RATE_LIMIT_EXCEEDED`` and
    ``METRICS_NOT_SUPPORTED`` are deprecated. Every code the API is known to
    send:

    ACCESS_DENIED, ACTION_FAILED, AI_DAILY_LIMIT_REACHED,
    AI_MAX_CONCURRENT_STREAMS, AI_NO_PLAN_LIMIT_REACHED, AI_UNAVAILABLE,
    AI_WEEKLY_LIMIT_REACHED, ANALYTICS_BUSY, APPLICATIONS_LIMIT_REACHED,
    APP_ALREADY_IN_WORKSPACE, APP_NOT_FOUND, BLOCKED_PATH, BRANCH_NOT_FOUND,
    CANNOT_EDIT_OWNER, CANNOT_INVITE_OWNER, CANNOT_LEAVE_OWNER,
    CANNOT_SET_SUBDOMAIN, CLUSTER_MAINTENANCE_TRY_LATER,
    CLUSTER_SELECTION_FAILED, CLUSTER_TIMEOUT, CLUSTER_UNAVAILABLE,
    COMMIT_FAILED, CONFLICTING_RESOURCES, CONTAINER_ALREADY_STARTED,
    CONTAINER_ALREADY_STOPPED, CONTAINER_INSUFFICIENT_DISK_SPACE,
    CONTAINER_NETWORK_CONFLICT, CONTAINER_NOT_FOUND,
    CONTAINER_TEMPORARILY_SUSPENDED, DAILY_SNAPSHOTS_LIMIT_REACHED,
    DATABASE_CREATION_FAILED, DATABASE_NOT_FOUND, DATABASE_NOT_RUNNING,
    DATABASE_UNAVAILABLE, DELETE_FAILED, DNS_FAILED, DOMAIN_ALREADY_EXISTS,
    EMPTY_RESPONSE, ENV_BUSY, ENV_CONTENT_TOO_LONG, ENV_NAME_TOO_LONG,
    FAILED_TO_FETCH, FILE_NOT_FOUND, FILE_TOO_LARGE, GITHUB_NOT_CONNECTED,
    GIT_ALREADY_CONFIGURED, GIT_BRANCH_DELETED, GIT_NOT_CONFIGURED,
    GIT_REF_NOT_SUPPORTED, INSUFFICIENT_MEMORY, INTERNAL_SERVER_ERROR,
    INVALID_ACCESS_TOKEN, INVALID_AUTORESTART, INVALID_BRANCH_LENGTH,
    INVALID_CODE, INVALID_CONTENT, INVALID_CONTENT_TYPE,
    INVALID_DATABASE_TYPE, INVALID_DATABASE_VERSION, INVALID_DESCRIPTION,
    INVALID_DISPLAY_NAME, INVALID_DOMAIN, INVALID_ENCODING,
    INVALID_ENV_CONTENT, INVALID_FILE, INVALID_FILENAME, INVALID_FILTER,
    INVALID_GROUP, INVALID_ID, INVALID_INPUT, INVALID_JSON_BODY,
    INVALID_MEMORY, INVALID_NAME, INVALID_PARAMETERS, INVALID_PATH,
    INVALID_RESET_TYPE, INVALID_SCOPE, INVALID_SNAPSHOT_ID,
    INVALID_SUBDOMAIN, INVALID_TIME_RANGE, INVALID_VERSION_ID, KEEP_CALM,
    LOAD_BALANCER_LIMIT_REACHED, LOGS_UNAVAILABLE, MEMBERS_LIMIT_REACHED,
    MEMBER_ALREADY_ADDED, MEMBER_NOT_FOUND, METRICS_NOT_SUPPORTED,
    MISSING_PARAMETERS, MISSING_REQUIRED_FIELDS, MISSING_SCOPE,
    NO_CUSTOM_DOMAIN, NO_UPDATE_DATA, PAYLOAD_TOO_LARGE, PERMISSION_DENIED,
    PURGE_CACHE_FAILED, RATE_LIMIT, RATE_LIMITED, RATE_LIMIT_EXCEEDED,
    READ_FAILED, REALTIME_MAX_CONNECTIONS, REALTIME_MAX_CONNECTIONS_APP,
    RENAME_FAILED, REPOSITORY_BRANCH_ALREADY_CONFIGURED,
    REPOSITORY_NOT_AVAILABLE, REPOSITORY_NOT_FOUND,
    REPOSITORY_PERMISSION_REQUIRED, REQUEST_ABORTED, RESERVED_DOMAIN,
    RESET_FAILED, RESOURCE_NOT_ALLOWED, RESTORE_INTERRUPTED,
    RESTORE_IN_PROGRESS, ROUTE_NOT_FOUND, SAVE_FAILED, SCOPE_NOT_GRANTABLE,
    SNAPSHOTS_UNAVAILABLE, SNAPSHOT_CORRUPT, SNAPSHOT_DATABASE_MISMATCH,
    SNAPSHOT_FAILED, SNAPSHOT_IN_PROGRESS, SNAPSHOT_NOT_FOUND,
    SNAPSHOT_PROCESSING, SNAPSHOT_RESTORE_FAILED,
    SNAPSHOT_RESTORE_PROCESSING, STATIC_APP_ENV_NOT_SUPPORTED,
    STORAGE_UPLOAD_FAILED, TOO_MANY_ENV_VARS, UNABLE_TO_FETCH_ANALYTICS,
    UNABLE_TO_FETCH_ERRORS, UNABLE_TO_FETCH_PERFORMANCE, UPGRADE_REQUIRED,
    UPLOAD_ABORTED, UPLOAD_BUSY, UPLOAD_FAILED, VALIDATION_FAILED,
    VALIDATION_TIMEOUT, WORKSPACE_CREATION_FAILED, WORKSPACE_LIMIT_REACHED,
    WORKSPACE_NOT_FOUND, WRITE_FAILED, WRONG_HOST.
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
        """The exception that caused this error, the same as ``__cause__``.

        It is set for a network error and for a successful response whose
        body is not JSON, and is ``None`` otherwise.
        """
        return self.__cause__

    def __str__(self) -> str:
        text = f'HTTP {self.status} {self.code}' if self.status else self.code
        if self.method:
            text = f'{self.method} {self.path}: {text}'
        return f'{text}: {self.message}' if self.message else text
