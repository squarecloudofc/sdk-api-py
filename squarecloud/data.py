from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Any


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
    time: int | None = None


@dataclass
class AppData:
    """application data class"""
    id: str
    name: str
    desc: str
    avatar: str
    owner: str
    cluster: Literal[
        'florida-ds1-1',
        'florida-ds1-2',
        'florida-ds1-3',
        'florida-ds1-free-1'
    ]
    cpu: int
    ram: int
    language: Literal[
        'javascript',
        'typescript',
        'python',
        'java',
        'rust',
        'go',
        'static',
        'dynamic',
    ]
    cluster: Literal['free-', 'florida-1']
    domain: str | None
    custom: str | None
    isWebsite: bool
    gitIntegration: bool


@dataclass
class UserData:
    """user data class"""
    id: int
    tag: str
    locale: str
    email: str | None
    plan: PlanData
    blocklist: bool


@dataclass
class LogsData:
    """logs data class"""
    logs: str | None

    def __eq__(self, other):
        return isinstance(other, LogsData) and self.logs == other.logs


@dataclass
class BackupData:
    """backup data class"""
    downloadURL: str


@dataclass
class UploadData:
    id: str
    tag: str
    language: str
    avatar: str
    ram: int
    cpu: int
    subdomain: str | None
    description: str | None


@dataclass
class FileInfo:
    type: Literal['file', 'directory']
    name: str
    size: int
    lastModified: int


@dataclass
class StatisticsData:
    users: int
    apps: int
    websites: int
    ping: int
    time: int
