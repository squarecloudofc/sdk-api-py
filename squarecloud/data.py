from __future__ import annotations

import os
import zipfile
from datetime import datetime
from typing import Any, Literal

from ._internal.constants import USING_PYDANTIC
from .http import HTTPClient

if USING_PYDANTIC:
    from pydantic.dataclasses import dataclass
else:
    from dataclasses import dataclass


class DataClasMeta(type):
    def __new__(cls, name: str, bases: tuple, dct: dict[str, Any]) -> type:
        new_class = super().__new__(cls, name, bases, dct)
        return dataclass(frozen=True)(new_class)


class BaseDataClass(metaclass=DataClasMeta):
    def to_dict(self) -> dict[str, str | dict[str, Any]]:
        return self.__dict__.copy()


class PlanData(BaseDataClass):
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
    memory: dict[str, Any]
    duration: int | None


class Language(BaseDataClass):
    name: str
    version: str


class StatusData(BaseDataClass):
    """
    Application status class

    :ivar cpu: the cpu used
    :ivar ram: the ram used
    :ivar status: the actual status of the application
    :ivar running: weather the application is running
    :ivar storage: storage used by the application
    :ivar network: network information
    :ivar uptime: uptime of the application
    :ivar time: time of the application

    :type cpu: str
    :type ram: str
    :type status: str
    :type running: bool
    :type storage: str
    :type network: Dict[str, Any]
    :type requests: conint(ge=0)
    :type uptime: int
    :type time: int | None = None
    """

    cpu: str
    ram: str
    status: str
    running: bool
    storage: str
    network: dict[str, Any]
    uptime: int | None = None
    time: int | None = None


class ResumedStatus(BaseDataClass):
    id: str
    running: bool
    cpu: str
    ram: str


class AppData(BaseDataClass):
    """
    Application data class

    :ivar id: The application ID
    :ivar name: The application name
    :ivar cluster: The cluster that the app is hosted on
    :ivar ram: The amount of RAM that application is using
    :ivar language The programming language of the app.:
    :ivar domain: The domain of the application
    :ivar custom: The custom domain of the application
    :ivar desc: The description of the application
    :ivar created_at: The date when the application was created

    :type id: str
    :type name: str
    :type cluster: str
    :type ram: confloat(ge=0);
    :type lang: str | None
    :type domain: str | None = None
    :type custom: str | None = None
    :type desc: str | None = None
    """

    id: str
    name: str
    cluster: str
    ram: float
    cluster: str
    created_at: datetime
    lang: str | None
    domain: str | None = None
    custom: str | None = None
    desc: str | None = None


class UserData(BaseDataClass):
    """
    User data class

    :ivar id: User ID;
    :ivar name: Username
    :ivar plan: User plan
    :ivar email: User email

    :type id: int
    :type name: str
    :type plan: PlanData
    :type email: str | None = None
    """

    id: int
    name: str
    plan: PlanData
    email: str | None = None
    locale: str | None = None


class LogsData(BaseDataClass):
    """Logs data class

    :ivar logs: A string containing logs of your application

    :type logs: str | str = ''
    """

    logs: str = ''

    def __eq__(self, other: object) -> bool:
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


class SnapshotInfo(BaseDataClass):
    name: str
    size: int
    modified: datetime
    key: str


class Snapshot:
    """
    Snapshot data class

    :ivar url: Url for download your Snapshot
    :ivar key: The Snapshot's key

    :type url: str
    :type key: str
    """

    __slots__ = ('url', 'key')

    def __init__(self, url: str, key: str) -> None:
        self.url = url
        self.key = key

    def to_dict(self) -> dict[str, str]:
        return {'url': self.url, 'key': self.key}

    async def download(self, path: str = './') -> zipfile.ZipFile:
        file_name = os.path.basename(self.url.split('?')[0])
        content = await HTTPClient.fetch_snapshot_content(self.url)
        with zipfile.ZipFile(f'{path}/{file_name}', 'w') as zip_file:
            zip_file.writestr(f'{path}/{file_name}', content)
            return zip_file


class UploadData(BaseDataClass):
    """
    Upload data class

    :ivar id: ID of the uploaded application
    :ivar name: Tag of the uploaded application
    :ivar language: Programming language of the uploaded application
    :ivar ram: Ram allocated for the uploaded application
    :ivar cpu: Cpu of the uploaded application
    :ivar description: Description of the uploaded application
    :ivar domain: Subdomain of the uploaded application (only in websites)
    :ivar cluster: Cluster where the application is hosted

    :type id: str
    :type name: str
    :type language: Language
    :type ram: confloat(ge=0)
    :type cpu: confloat(ge=0)
    :type domain: str | None = None
    :type description: str | None = None
    :type cluster: str
    """

    id: str
    name: str
    language: Language
    ram: float
    cpu: float
    cluster: str
    domain: str | None = None
    description: str | None = None


class FileInfo(BaseDataClass):
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
    :type lastModified: int | float | None
    :type path: str
    """

    app_id: str
    type: Literal['file', 'directory']
    name: str
    path: str
    size: int = 0
    lastModified: int | float | None = None # noqa: N815: Ignore mixedCase naming convention


class DeployData(BaseDataClass):
    id: str
    state: str
    date: datetime


class DomainAnalytics(BaseDataClass):
    class BaseAnalytics(BaseDataClass):
        visits: int
        requests: int
        bytes: int
        date: str
        @property
        def date_time(self) -> datetime:
            "retrieves the date as a datetime object"
            return datetime.fromisoformat(self.date)
    class ExtraBaseAnalytics(BaseAnalytics):
        type: str
    class Visits(BaseAnalytics):
        pass
    class Countries(ExtraBaseAnalytics):
        pass
    class Devices(ExtraBaseAnalytics):
        pass
    class Os(ExtraBaseAnalytics):
        pass
    class Browsers(ExtraBaseAnalytics):
        pass
    class Protocols(ExtraBaseAnalytics):
        pass
    class Methods(ExtraBaseAnalytics):
        pass
    class Paths(ExtraBaseAnalytics):
        pass
    class Referers(ExtraBaseAnalytics):
        pass
    class Providers(ExtraBaseAnalytics):
        pass
    visits: list[Visits]
    countries: list[Countries]
    devices: list[Devices]
    os: list[Os]
    browsers: list[Browsers]
    protocols: list[Protocols]
    methods: list[Methods]
    paths: list[Paths]
    referers: list[Referers]
    providers: list[Providers]


class DNSRecord(BaseDataClass):
    type: str
    name: str
    value: str
    status: str
