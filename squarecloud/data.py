from dataclasses import dataclass
from typing import Dict, Literal, Any, Optional
# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name


@dataclass
class PlanData:
    """plan data class"""
    name: str
    memory: Dict[str, Any]
    duration: Dict[str, Any]


@dataclass
class StatusData:
    """application status class"""
    cpu: str
    ram: str
    status: Literal['created', 'starting', 'restarting', 'running', 'deleting']
    running: bool
    storage: str
    network: Dict[str, Any]
    requests: int
    uptime: int
    time: Optional[int] = None


@dataclass
class AppData:
    """application data class"""
    id: int | str
    tag: str
    ram: int
    lang: Literal['javascript', 'typescript', 'python', 'java']
    type: Literal['free', 'paid']
    cluster: Literal['free-', 'florida-1']
    isWebsite: bool
    avatar: str


@dataclass
class UserData:
    """user data class"""
    id: int
    tag: str
    email: str | Literal['Access denied']
    plan: PlanData
    blocklist: bool


@dataclass
class LogsData:
    """logs data class"""
    logs: str


@dataclass
class CompleteLogsData:
    """complete logs data class"""
    logs: str


@dataclass
class BackupData:
    """backup data class"""
    downloadURL: str
