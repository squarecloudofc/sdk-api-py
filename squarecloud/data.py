from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal

# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name


@dataclass
class PlanData:
    """
    Plan data class

    :ivar name: The plan name
    :ivar memory: The plan memory available
    :ivar duration: Plan duration

    :type name: str
    :type memory: Dict[str, Any]
    :type duration: Dict[str, Any]
    """

    name: str
    memory: Dict[str, Any]
    duration: Dict[str, Any]


@dataclass
class StatusData:
    """
    Application status class

    :ivar cpu: the cpu used
    :ivar ram: the ram used
    :ivar status: the actual status of the application
    :ivar running: weather the application is running
    :ivar storage: storage used by the application
    :ivar network: network information
    :ivar requests: requests made by the application
    :ivar uptime: uptime of the application
    :ivar time: time of the application

    :type cpu: str
    :type ram: str
    :type status: Literal[
        'created',
        'starting',
        'restarting',
        'running',
        'deleting'
        ]
    :type running: bool
    :type storage: str
    :type network: Dict[str, Any]
    :type requests: int
    :type uptime: int
    :type time: int | None = None
    """

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
    """
    Application data class

    :ivar id: The application ID
    :ivar name: The application name
    :ivar avatar: The application avatar
    :ivar owner: The application owner ID
    :ivar cluster: The cluster that the app is hosted on
    :ivar cpu: The amount of CPU that application is using
    :ivar ram: The amount of RAM that application is using
    :ivar language The programming language of the app.:
    :ivar isWebsite: Whether if the app is a website

    :type id: str
    :type name: str
    :type avatar: str
    :type owner: str
    :type cluster: Literal[
        'florida-ds1-1', 'florida-ds1-2', 'florida-ds1-3', 'florida-ds1-free-1'
    ]
    :type cpu: int;
    :type ram: int;
    :type language: Literal[
        'javascript',
        'typescript',
        'python',
        'java',
        'rust',
        'go',
        'static',
        'dynamic',
    ]
    :type isWebsite: bool
    :type gitIntegration: bool
    :type domain: str | None = None
    :type custom: str | None = None
    :type desc: str | None = None
    """

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
    """
    User data class

    :ivar id: User ID;
    :ivar tag: User name
    :ivar locale: User locale
    :ivar plan: User plan
    :ivar blocklist: Whether to user is blocked
    :ivar email: User email

    :type id: int
    :type tag: str
    :type locale: str
    :type plan: PlanData
    :type blocklist: bool
    :type email: str | None = None
    """

    id: int
    tag: str
    locale: str
    plan: PlanData
    blocklist: bool
    email: str | None = None


@dataclass
class LogsData:
    """Logs data class

    :ivar logs: A string containing logs of your application

    :type logs: str | str = ''
    """

    logs: str = ''

    def __eq__(self, other) -> bool:
        """
        The __eq__ function is a special function that allows us to compare
        two objects of the same class.
        In this case, we are comparing two LogsData objects. The __eq__
        function returns True if the logs
        of both LogsData objects are equal and False otherwise.

        Example:

        ````{.py3 hl_lines="15 21" linenums="1" title="example_2.py"}
        from time import sleep

        import squarecloud as square

        client = square.Client(api_key='API KEY')


        async def example():
            app = await client.app('application id')

            logs1 = await app.logs() # 'Hello World'

            logs2 = await app.logs() # 'Hello World'

            print(logs1 == logs2) # True

            sleep(10)

            logs3 = await app.logs() # 'Hello World, I'm beautifully'

            print(logs1 == logs3) # False
        ````

        :param self: Refer to the object itself
        :param other: Compare the current instance of LogsData to another
        instance of LogsData
        :return: A boolean value that is true if the two objects are equal and
        false otherwise
        :rtype: bool
        """
        return isinstance(other, LogsData) and self.logs == other.logs


@dataclass
class BackupData:
    """
    Backup data class

    :ivar downloadURL: Url for download your backup

    :type downloadURL: str
    """

    downloadURL: str


@dataclass
class UploadData:
    """
    Upload data class

    :ivar id: ID of the uploaded application
    :ivar tag: Tag of the uploaded application
    :ivar language: Programming language of the uploaded application
    :ivar avatar: Avatar of the uploaded application
    :ivar ram: Ram allocated for the uploaded application
    :ivar cpu: Cpu of the uploaded application
    :ivar description: Description of the uploaded application
    :ivar subdomain: Subdomain of the uploaded application (only in websites)

    :type id: str
    :type tag: str
    :type language: str
    :type avatar: str
    :type ram: int
    :type cpu: int
    :type subdomain: str | None = None
    :type description: str | None = None
    """

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
    """
    File information

    :ivar type: return type of file
    :ivar name: File/Directory name
    :ivar size: File size
    :ivar lastModified: Last modification time
    :ivar path: File/Directory path

    :type type: Literal['file', 'directory']
    :type name: str
    :type size: int
    :type lastModified: int | float
    :type path: str
    """

    type: Literal['file', 'directory']
    name: str
    size: int
    lastModified: int | float
    path: str


@dataclass
class StatisticsData:
    """
    Host statistics

    :ivar users: Amount of users that uses the host
    :ivar apps: Amount of apps hosted
    :ivar websites: Amount of websites hosted
    :ivar ping: Service ping
    :ivar time: Time

    :type users: int
    :type apps: int
    :type websites: int
    :type ping: int
    :type time: int
    """

    users: int
    apps: int
    websites: int
    ping: int
    time: int
