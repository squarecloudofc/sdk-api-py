from .data import AppData
from abc import ABC
from typing import Literal, TYPE_CHECKING, Callable
from .square import File
from .data import StatusData, LogsData, FullLogsData, BackupData
from .http import Response, HTTPClient, Endpoint
from .errors import SquareException
from .listener import ListenerManager

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
        '_client',
        '_http',
        '_listener',
        '_data',
        'cache'
    ]

    def __init__(self, client: 'Client', http: HTTPClient, data: AppData):
        self._client: 'Client' = client
        self._http = http
        self._listener: ListenerManager = ListenerManager(self)
        self._data = data
        self.cache: AppCache = AppCache()

    def __repr__(self):
        return f'<{self.__class__.__name__} tag={self.tag} id={self.id}>'

    @property
    def data(self):
        return self._data

    @property
    def client(self):
        """client instance"""
        return self._client

    @property
    def id(self):
        """application's id"""
        return self.data.id

    @property
    def tag(self):
        """application's tag"""
        return self.data.tag

    @property
    def ram(self):
        """application's allocated ram"""
        return self.data.ram

    @property
    def lang(self):
        """application's programing language"""
        return self.data.lang

    @property
    def type(self):
        """application's type"""
        return self.data.type

    @property
    def cluster(self):
        """application's cluster"""
        return self.data.cluster

    @property
    def is_website(self):
        """whether the application is a website"""
        return self.data.isWebsite

    @property
    def avatar(self):
        """application's avatar"""
        return self.data.avatar

    def on_request(self, endpoint: Endpoint) -> Callable:
        def wrapper(func):
            self._listener.add_listener(endpoint, func)

        return wrapper

    async def logs(self, update_cache: bool = True) -> LogsData:
        """get application's logs"""
        logs: LogsData = await self.client.get_logs(self.id)
        endpoint: Endpoint = Endpoint.logs()
        await self._listener.on_request_end(endpoint=endpoint, logs=logs)
        if update_cache:
            self.cache.logs = logs
        return logs

    async def full_logs(self, update_cache: bool = True) -> FullLogsData:
        """get application's full logs"""
        full_logs: FullLogsData = await self.client.full_logs(self.id)
        endpoint: Endpoint = Endpoint.full_logs()
        await self._listener.on_request_end(
            endpoint=endpoint, full_logs=full_logs)
        if update_cache:
            self.cache.full_logs = full_logs
        return full_logs

    async def status(self, update_cache: bool = True) -> StatusData:
        """get application's status"""
        status: StatusData = await self.client.app_status(self.id)
        endpoint: Endpoint = Endpoint.app_status()
        await self._listener.on_request_end(endpoint=endpoint, status=status)
        if update_cache:
            self.cache.status = status
        return status

    async def backup(self, update_cache: bool = True) -> BackupData:
        """make backup of this application"""
        backup: BackupData = await self.client.backup(self.id)
        endpoint: Endpoint = Endpoint.backup()
        await self._listener.on_request_end(endpoint=endpoint, backup=backup)
        if update_cache:
            self.cache.backup = backup
        return backup

    async def start(self, update_cache: bool = True) -> Response:
        """start the application"""
        if update_cache:
            self.cache.status.running = True
        return await self.client.start_app(self.id)

    async def stop(self, update_cache: bool = True) -> Response:
        """stop the application"""
        result = await self.client.stop_app(self.id)
        if update_cache:
            self.cache.status.running = False
        return result

    async def restart(self, update_cache: bool = True) -> Response:
        """restart the application"""
        result = await self.client.restart_app(self.id)
        if update_cache:
            self.cache.status.status = 'restarting'
        return result

    async def delete(self) -> Response:
        """delete the application"""
        return await self.client.delete_app(self.id)

    async def commit(self, file: File) -> Response:
        """commit the application"""
        return await self.client.commit(self.id, file=file)
