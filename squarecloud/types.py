from typing import Any, Dict, Optional, Literal, TypedDict


class RawResponseData(TypedDict):
    """raw response data"""
    data: Dict[str, Any]
    response: Dict[str, Any]
    status: Literal['success', 'error']
    code: Optional[int]
    message: Optional[str]
    statusCode: Optional[str]
    error: Optional[str]


class UserPayload(RawResponseData):
    """user payload"""
    user: Dict[str, Any]
    applications: Dict[str, Any]


class LogsPayload(RawResponseData):
    """logs payload"""
    logs: Dict[str, Any]


class BackupPayload(RawResponseData):
    """backup payload"""
    backup: Dict[str, Any]


class CompleteLogsPayload(RawResponseData):
    """complete logs payload"""
    url: Dict[str, Any]


class StatusPayload(RawResponseData):
    """status payload"""
    # pylint: disable=invalid-name
    app_status: Dict[str, Any]


class StopPayload(RawResponseData):
    """stop payload"""
    stop: Dict[str, Any]
