from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import confloat, conint
from pydantic.dataclasses import dataclass

# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name


@dataclass(frozen=True)
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
    duration: Dict[str, Any] | None

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
class Language:
    name: str
    version: str


@dataclass(frozen=True)
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
    :type status: str
    :type running: bool
    :type storage: str
    :type network: Dict[str, Any]
    :type requests: conint(ge=0)
    :type uptime: conint(ge=0)
    :type time: conint(ge=0) | None = None
    """

    cpu: str
    ram: str
    status: str
    running: bool
    storage: str
    network: Dict[str, Any]
    requests: conint(ge=0)
    uptime: conint(ge=0) | None = None
    time: conint(ge=0) | None = None

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
class AppData:
    """
    Application data class

    :ivar id: The application ID
    :ivar name: The application name
    :ivar cluster: The cluster that the app is hosted on
    :ivar ram: The amount of RAM that application is using
    :ivar language The programming language of the app.:

    :type id: str
    :type name: str
    :type cluster: str
    :type ram: confloat(ge=0);
    :type language: Language
    :type domain: str | None = None
    :type custom: str | None = None
    :type desc: str | None = None
    """

    id: str
    name: str
    cluster: str
    ram: confloat(ge=0)
    language: Optional[str]
    cluster: str
    domain: str | None = None
    custom: str | None = None
    desc: str | None = None

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
class UserData:
    """
    User data class

    :ivar id: User ID;
    :ivar name: Username
    :ivar plan: User plan
    :ivar email: User email

    :type id: conint(ge=0)
    :type name: str
    :type plan: PlanData
    :type email: str | None = None
    """

    id: conint(ge=0)
    name: str
    plan: PlanData
    email: str | None = None

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
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

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
class BackupData:
    """
    Backup data class

    :ivar downloadURL: Url for download your backup

    :type downloadURL: str
    """

    downloadURL: str

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
class UploadData:
    """
    Upload data class

    :ivar id: ID of the uploaded application
    :ivar name: Tag of the uploaded application
    :ivar language: Programming language of the uploaded application
    :ivar ram: Ram allocated for the uploaded application
    :ivar cpu: Cpu of the uploaded application
    :ivar description: Description of the uploaded application
    :ivar subdomain: Subdomain of the uploaded application (only in websites)

    :type id: str
    :type name: str
    :type language: Language
    :type ram: confloat(ge=0)
    :type cpu: confloat(ge=0)
    :type subdomain: str | None = None
    :type description: str | None = None
    """

    id: str
    name: str
    language: Language
    ram: confloat(ge=0)
    cpu: confloat(ge=0)
    subdomain: str | None = None
    description: str | None = None

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
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
    :type size: confloat(ge=0)
    :type lastModified: conint(ge=0) | float
    :type path: str
    """

    app_id: str
    type: Literal['file', 'directory']
    name: str
    lastModified: conint(ge=0) | float
    path: str
    size: confloat(ge=0.0) = 0.0

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
class DeployData:
    id: str
    state: str
    date: datetime

    def to_dict(self):
        return self.__dict__.copy()


@dataclass(frozen=True)
class DomainAnalytics:
    hostname: str
    total: list[Any]
    countries: list[Any]
    methods: list[Any]
    referers: list[Any]
    browsers: list[Any]
    deviceTypes: list[Any]
    operatingSystems: list[Any]
    agents: list[Any]
    hosts: list[Any]
    paths: list[Any]

    def to_dict(self):
        return self.__dict__.copy()
