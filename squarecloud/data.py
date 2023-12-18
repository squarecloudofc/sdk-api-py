from __future__ import annotations

from typing import Any, Dict, Literal

from pydantic import BaseModel

# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name


class PlanData(BaseModel):
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


class Language(BaseModel):
    name: str
    version: str


class StatusData(BaseModel):
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
    :type requests: int
    :type uptime: int
    :type time: int | None = None
    """

    cpu: str
    ram: str
    status: str
    running: bool
    storage: str
    network: Dict[str, Any]
    requests: int
    uptime: int | None = None
    time: int | None = None


class AppData(BaseModel):
    """
    Application data class

    :ivar id: The application ID
    :ivar name: The application name
    :ivar owner: The application owner ID
    :ivar cluster: The cluster that the app is hosted on
    :ivar ram: The amount of RAM that application is using
    :ivar language The programming language of the app.:
    :ivar isWebsite: Whether if the app is a website

    :type id: str
    :type name: str
    :type owner: str
    :type cluster: str
    :type ram: int;
    :type language: Language
    :type isWebsite: bool
    :type gitIntegration: bool
    :type domain: str | None = None
    :type custom: str | None = None
    :type desc: str | None = None
    """

    id: str
    name: str
    owner: str
    cluster: str
    ram: int
    language: str
    cluster: str
    isWebsite: bool
    gitIntegration: bool
    domain: str | None = None
    custom: str | None = None
    desc: str | None = None


class UserData(BaseModel):
    """
    User data class

    :ivar id: User ID;
    :ivar tag: Username
    :ivar plan: User plan
    :ivar blocklist: Whether to user is blocked
    :ivar email: User email

    :type id: int
    :type tag: str
    :type plan: PlanData
    :type email: str | None = None
    """

    id: int
    tag: str
    plan: PlanData
    email: str | None = None


class LogsData(BaseModel):
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


class BackupData(BaseModel):
    """
    Backup data class

    :ivar downloadURL: Url for download your backup

    :type downloadURL: str
    """

    downloadURL: str


class UploadData(BaseModel):
    """
    Upload data class

    :ivar id: ID of the uploaded application
    :ivar tag: Tag of the uploaded application
    :ivar language: Programming language of the uploaded application
    :ivar ram: Ram allocated for the uploaded application
    :ivar cpu: Cpu of the uploaded application
    :ivar description: Description of the uploaded application
    :ivar subdomain: Subdomain of the uploaded application (only in websites)

    :type id: str
    :type tag: str
    :type language: Language
    :type ram: int
    :type cpu: int
    :type subdomain: str | None = None
    :type description: str | None = None
    """

    id: str
    tag: str
    language: Language
    ram: int
    cpu: int
    subdomain: str | None = None
    description: str | None = None


class FileInfo(BaseModel):
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


class StatisticsData(BaseModel):
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
