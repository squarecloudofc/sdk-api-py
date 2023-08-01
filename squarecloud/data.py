from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal

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
    avatar: str
    owner: str
    cluster: Literal[
        'florida-ds1-1', 'florida-ds1-2', 'florida-ds1-3', 'florida-ds1-free-1'
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
    isWebsite: bool
    gitIntegration: bool
    domain: str | None = None
    custom: str | None = None
    desc: str | None = None


@dataclass
class UserData:
    """user data class"""

    id: int
    tag: str
    locale: str
    plan: PlanData
    blocklist: bool
    email: str | None = None


@dataclass
class LogsData:
    """logs data class"""

    logs: str | None = None

    def __eq__(self, other):
        """
        The __eq__ function is a special function that allows us to compare
        two objects of the same class.
        In this case, we are comparing two LogsData objects. The __eq__
        function returns True if the logs
        of both LogsData objects are equal and False otherwise.

        :param self: Refer to the object itself
        :param other: Compare the current instance of LogsData to another
        instance of LogsData
        :return: A boolean value that is true if the two objects are equal and
        false otherwise
        """
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
    subdomain: str | None = None
    description: str | None = None


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
