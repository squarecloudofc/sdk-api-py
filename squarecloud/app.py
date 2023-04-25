from abc import ABC
from io import BytesIO
from typing import TYPE_CHECKING, Callable, Literal

from .data import StatusData, LogsData, BackupData, AppData, FileInfo
from .errors import SquareException
from .http import Response, HTTPClient, Endpoint
from .listener import ListenerManager, Listener
from .square import File

# avoid circular imports
if TYPE_CHECKING:
    from .client import Client


class AppCache:
    __slots__ = (
        'status',
        'logs',
        'backup',
        'data',
    )

    def __init__(self):
        self.status: StatusData | None = None
        self.logs: LogsData | None = None
        self.backup: BackupData | None = None
        self.data: AppData | None = None

    def clear(self):
        self.status = None
        self.logs = None
        self.backup = None
        self.data = None

    def update(self, *args):
        for arg in args:
            if isinstance(arg, StatusData):
                self.status = arg
            elif isinstance(arg, LogsData):
                self.logs = arg
            elif isinstance(arg, BackupData):
                self.backup = arg
            elif isinstance(arg, AppData):
                self.data = arg
            else:
                types: list = [
                    i.__name__ for i in [
                        StatusData,
                        LogsData,
                        BackupData,
                        AppData,
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
        '_id',
        '_tag',
        '_desc',
        '_ram',
        '_lang',
        '_type',
        '_cluster',
        '_isWebsite',
        '_avatar',
    ]

    def __init__(
            self,
            client: 'Client',
            http: HTTPClient,
            id: str,
            tag: str,
            desc: str,
            ram: int,
            lang: Literal[
                'javascript',
                'typescript',
                'python',
                'java',
                'rust',
                'go',
                'static',
                'dynamic',
            ],
            type: Literal['free', 'paid'],
            cluster: Literal['free-', 'florida-1'],
            isWebsite: bool,
            avatar: str,
    ):
        self._id = id
        self._tag = tag
        self._desc = desc
        self._ram = ram
        self._lang = lang
        self._type = type
        self._cluster = cluster
        self._isWebsite = isWebsite
        self._avatar = avatar
        self._client: 'Client' = client
        self._http = http
        self._listener: ListenerManager = Listener
        self.cache: AppCache = AppCache()

    def __repr__(self):
        return f'<{self.__class__.__name__} tag={self.tag} id={self.id}>'

    @property
    def client(self):
        """client instance"""
        return self._client

    @property
    def id(self):
        """application's id"""
        return self._id

    @property
    def tag(self):
        """application's tag"""
        return self._tag

    @property
    def desc(self):
        return self._desc

    @property
    def ram(self):
        """application's allocated ram"""
        return self._ram

    @property
    def lang(self):
        """application's programing language"""
        return self._lang

    @property
    def type(self):
        """application's type"""
        return self._type

    @property
    def cluster(self):
        """application's cluster"""
        return self._cluster

    @property
    def is_website(self):
        """whether the application is a website"""
        return self._isWebsite

    @property
    def avatar(self):
        """application's avatar"""
        return self._avatar

    def capture(self, endpoint: Endpoint) -> Callable:
        allowed_endpoints: tuple[Endpoint, Endpoint, Endpoint, Endpoint] = (
            Endpoint.logs(),
            Endpoint.app_status(),
            Endpoint.backup(),
            Endpoint.app_data()
        )

        def wrapper(func):
            if endpoint not in allowed_endpoints:
                raise SquareException(
                    f'the endpoint to capture must be {allowed_endpoints}')

            if not self._listener.get_capture_listener(endpoint):
                return self._listener.add_capture_listener(endpoint, func)
            raise SquareException(
                f'Already exists an capture_listener for {endpoint}')

        return wrapper

    async def data(self, **kwargs):
        app_data: AppData = await self.client.app_data(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.app_data()
            await self._listener.on_capture(
                endpoint=endpoint,
                before=self.cache.data,
                after=app_data,
            )
        if kwargs.get('update_cache', True):
            self.cache.update(app_data)
        return app_data

    async def logs(self, **kwargs) -> LogsData:
        """get application's logs"""
        logs: LogsData = await self.client.get_logs(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.logs()
            await self._listener.on_capture(endpoint=endpoint,
                                            before=self.cache.logs, after=logs)
        if kwargs.get('update_cache', True):
            self.cache.update(logs)
        return logs

    async def status(self, **kwargs) -> StatusData:
        """get application's status"""
        status: StatusData = await self.client.app_status(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.app_status()
            await self._listener.on_capture(endpoint=endpoint,
                                            before=self.cache.status,
                                            after=status)
        if kwargs.get('update_cache', True):
            self.cache.update(status)
        return status

    async def backup(self, **kwargs) -> BackupData:
        """make backup of this application"""
        backup: BackupData = await self.client.backup(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.backup()
            await self._listener.on_capture(endpoint=endpoint,
                                            before=self.cache.backup,
                                            after=backup)
        if kwargs.get('update_cache', True):
            self.cache.update(backup)
        return backup

    async def start(self, **kwargs) -> Response:
        """start the application"""
        response: Response = await self.client.start_app(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.start()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def stop(self, **kwargs) -> Response:
        """stop the application"""
        response: Response = await self.client.stop_app(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.stop()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def restart(self, **kwargs) -> Response:
        """restart the application"""
        response: Response = await self.client.restart_app(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.restart()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def delete(self, **kwargs) -> Response:
        """delete the application"""
        response: Response = await self.client.delete_app(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.delete_app()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def commit(self, file: File,
                     **kwargs) -> Response:
        """commit the application"""
        response: Response = await self.client.commit(self.id, file=file)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.commit()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def files_list(self, path: str, **kwargs):
        response: list[FileInfo] = await self.client.app_files_list(self.id,
                                                                    path)

        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.files_list()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def read_file(self, path: str, **kwargs):
        response: BytesIO = await self.client.read_app_file(self.id, path)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.files_read()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response

    async def create_file(self, path: str, **kwargs):
        response: None = await self.client.read_app_file(self.id, path)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.files_read()
            await self._listener.on_capture(endpoint=endpoint,
                                            response=response)
        return response
