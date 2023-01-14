from .data import AppData
from abc import ABC
from typing import Literal, TYPE_CHECKING
from .square import File
from .data import StatusData, LogsData, FullLogsData, BackupData
from .http import Response
from .errors import SquareException

# avoid circular imports
if TYPE_CHECKING:
    from .client import Client


class AppCache:
    def __init__(self):
        self.status: StatusData | None = None
        self.logs: LogsData | None = None
        self.full_logs: FullLogsData | None = None
        self.backup: BackupData | None = None

    def clear(self):
        self.status = None
        self.logs = None
        self.full_logs = None
        self.backup = None

    def update(self, *args):
        for arg in args:
            if isinstance(arg, StatusData):
                self.status = arg
            elif isinstance(arg, LogsData):
                self.logs = arg
            elif isinstance(arg, FullLogsData):
                self.full_logs = arg
            elif isinstance(arg, BackupData):
                self.backup = arg
            else:
                types: list = [
                    i.__name__ for i in [
                        StatusData,
                        LogsData,
                        FullLogsData,
                        BackupData,
                    ]
                ]
                raise SquareException(
                    f'you must provide stats of the following types:\n{types}')


class AbstractApplication(ABC):
    """Abstract application class"""


class Application(AbstractApplication):
    """Represents an application"""
    # pylint: disable=too-many-instance-attributes
    # nine arguments is available in this case
    # pylint: disable=invalid-name
    __slots__ = [
        '__client',
        '__http',
        '__id',
        '__tag',
        '__ram',
        '__lang',
        '__type',
        '__cluster',
        '__is_website',
        '__avatar',
        'cache'
    ]

    def __init__(self, client: 'Client', data: AppData):
        self.__client: Client = client
        self.__id: str = data.id
        self.__tag: str = data.tag
        self.__ram: int = data.ram
        self.__lang: Literal['javascript', 'typescript', 'python'] = data.lang
        self.__type: Literal['free', 'paid'] = data.type
        self.__cluster: str = data.cluster
        self.__is_website: bool = data.isWebsite
        self.__avatar: str = data.avatar
        self.cache: AppCache = AppCache()

    def __repr__(self):
        return f'<{self.__class__.__name__} tag={self.tag} id={self.id}>'

    @property
    def client(self):
        """client instance"""
        return self.__client

    @property
    def id(self):
        """application's id"""
        return self.__id

    @property
    def tag(self):
        """application's tag"""
        return self.__tag

    @property
    def ram(self):
        """application's allocated ram"""
        return self.__ram

    @property
    def lang(self):
        """application's programing language"""
        return self.__lang

    @property
    def type(self):
        """application's type"""
        return self.__type

    @property
    def cluster(self):
        """application's cluster"""
        return self.__cluster

    @property
    def is_website(self):
        """whether the application is a website"""
        return self.__is_website

    @property
    def avatar(self):
        """application's avatar"""
        return self.__avatar

    async def logs(self, update_cache: bool = True) -> LogsData:
        """get application's logs"""
        logs: LogsData = await self.__client.get_logs(self.id)
        if update_cache:
            self.cache.logs = logs
        return logs

    async def full_logs(self, update_cache: bool = True) -> FullLogsData:
        """get application's full logs"""
        full_logs: FullLogsData = await self.__client.logs_complete(self.id)
        if update_cache:
            self.cache.full_logs = full_logs
        return full_logs

    async def status(self, update_cache: bool = True) -> StatusData:
        """get application's status"""
        status: StatusData = await self.__client.app_status(self.id)
        if update_cache:
            self.cache.status = status
        return status

    async def backup(self, update_cache: bool = True) -> BackupData:
        """make backup of this application"""
        backup: BackupData = await self.__client.backup(self.id)
        if update_cache:
            self.cache.backup = backup
        return backup

    async def start(self, update_cache: bool = True) -> Response:
        """start the application"""
        if update_cache:
            self.cache.status.running = True
        return await self.__client.start_app(self.id)

    async def stop(self, update_cache: bool = True) -> Response:
        """stop the application"""
        result = await self.__client.stop_app(self.id)
        if update_cache:
            self.cache.status.running = False
        return result

    async def restart(self, update_cache: bool = True) -> Response:
        """restart the application"""
        result = await self.__client.restart_app(self.id)
        if update_cache:
            self.cache.status.status = 'restarting'
        return result

    async def delete(self) -> Response:
        """delete the application"""
        return await self.__client.delete_app(self.id)

    async def commit(self, file: File) -> Response:
        """commit the application"""
        return await self.__client.commit(self.id, file=file)
