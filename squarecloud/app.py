from abc import ABC
from typing import TYPE_CHECKING, Callable

from .data import AppData
from .data import StatusData, LogsData, FullLogsData, BackupData
from .errors import SquareException
from .http import Response, HTTPClient, Endpoint
from .listener import ListenerManager, Listener
from .square import File

# avoid circular imports
if TYPE_CHECKING:
    from .client import Client


class AppCache:
    def __init__(self):
        self.status: StatusData | None = None
        self.logs: LogsData = LogsData(logs=None)
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
        self._listener: ListenerManager = Listener
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

    def capture(self, endpoint: Endpoint) -> Callable:
        def wrapper(func):
            if not self._listener.get_capture_listener(endpoint):
                return self._listener.add_capture_listener(endpoint, func)
            raise SquareException(
                f'Already exists an capture_listener for {endpoint}')

        return wrapper

    async def logs(self, avoid_listener: bool = False) -> LogsData:
        """get application's logs"""
        logs: LogsData = await self.client.get_logs(self.id)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.logs()
            await self._listener.on_capture(endpoint=endpoint,
                                            before=self.cache.logs, after=logs)
        return logs

    async def full_logs(self, avoid_listener: bool = False) -> FullLogsData:
        """get application's full logs"""
        full_logs: FullLogsData = await self.client.full_logs(self.id)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.full_logs()
            await self._listener.on_capture(endpoint=endpoint,
                                            before=self.cache.full_logs,
                                            after=full_logs)
        return full_logs

    async def status(self, avoid_listener: bool = False) -> StatusData:
        """get application's status"""
        status: StatusData = await self.client.app_status(self.id)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.app_status()
            await self._listener.on_capture(endpoint=endpoint,
                                            before=self.cache.status,
                                            after=status)
        return status

    async def backup(self, avoid_listener: bool = False) -> BackupData:
        """make backup of this application"""
        backup: BackupData = await self.client.backup(self.id)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.backup()
            await self._listener.on_capture(endpoint=endpoint,
                                            before=self.cache.backup,
                                            after=backup)
        return backup

    async def start(self, avoid_listener: bool = False) -> Response:
        """start the application"""
        response: Response = await self.client.start_app(self.id)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.start()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def stop(self, avoid_listener: bool = False) -> Response:
        """stop the application"""
        response: Response = await self.client.stop_app(self.id)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.stop()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def restart(self, avoid_listener: bool = False) -> Response:
        """restart the application"""
        response: Response = await self.client.restart_app(self.id)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.restart()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def delete(self, avoid_listener: bool = False) -> Response:
        """delete the application"""
        response: Response = await self.client.delete_app(self.id)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.delete_app()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def commit(self, file: File,
                     avoid_listener: bool = False) -> Response:
        """commit the application"""
        response: Response = await self.client.commit(self.id, file=file)
        if not avoid_listener:
            endpoint: Endpoint = Endpoint.commit()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response
