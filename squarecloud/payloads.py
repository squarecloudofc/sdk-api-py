from typing import Any, Literal, Optional, TypedDict


class RawResponseData(TypedDict):
    """raw response data"""

    data: dict[str, Any]
    response: dict[str, Any]
    headers: dict[str, Any]
    status: Literal['success', 'error']
    code: Optional[int]
    message: Optional[str]
    statusCode: Optional[str]
    error: Optional[str]
    app: Optional[dict[str, Any]]


class UserPayload(RawResponseData):
    """user payload"""

    user: dict[str, Any]
    applications: list[dict[str, Any]]


class LogsPayload(RawResponseData):
    """logs payload"""

    logs: dict[str, Any]


class BackupPayload(RawResponseData):
    """backup payload"""

    backup: dict[str, Any]


class StatusPayload(RawResponseData):
    """status payload"""

    # pylint: disable=invalid-name
    app_status: dict[str, Any]


class StopPayload(RawResponseData):
    """stop payload"""

    stop: dict[str, Any]


class UploadPayload(RawResponseData):
    app: dict[str, Any]
