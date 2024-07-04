from __future__ import annotations

from functools import wraps
from io import BytesIO
from typing import TYPE_CHECKING, Any, Callable

from pydantic import PositiveInt

from squarecloud import errors

from .data import (
    AppData,
    BackupData,
    DeployData,
    DomainAnalytics,
    FileInfo,
    LogsData,
    StatusData,
)
from .file import File
from .http import Endpoint, HTTPClient, Response
from .listeners import Listener, ListenerConfig
from .listeners.capture_listener import CaptureListenerManager

# avoid circular imports
if TYPE_CHECKING:
    from .client import Client


class AppCache:
    __slots__ = (
        '_status',
        '_logs',
        '_backup',
        '_app_data',
    )

    def __init__(self) -> None:
        """
        The `__init__` function is called when the class is instantiated.
        It sets up the instance of the class, and defines all of its
        attributes.


        :return: None
        """
        self._status: StatusData | None = None
        self._logs: LogsData | None = None
        self._backup: BackupData | None = None
        self._app_data: AppData | None = None

    @property
    def status(self) -> StatusData:
        """
        The status method is a property that returns the cached StatusData of
        the application.

        :return: A StatusData object.
        :rtype: StatusData
        """
        return self._status

    @property
    def logs(self) -> LogsData:
        """
        The logs method is a property that returns the cached LogsData of
        the application.

        :return: The logs of your application
        :rtype: LogsData
        """
        return self._logs

    @property
    def backup(self) -> BackupData:
        """
        The backup method is a property that returns the cached BackupData of
        the application.

        :return: The value of the _backup attribute
        :rtype: BackupData
        """
        return self._backup

    @property
    def app_data(self) -> AppData:
        """
        The app_data method is a property that returns the cached AppData
        object

        :return: The data from the app_data
        :rtype: AppData
        """
        return self._app_data

    def clear(self):
        """
        The clear method is used to clear the status, logs, backup and data
        variables.

        :param self: Refer to the class instance
        :return: None
        """
        self._status = None
        self._logs = None
        self._backup = None
        self._app_data = None

    def update(self, *args):
        """
        The update method is used to update the data of a given instance.
        It takes in an arbitrary number of arguments, and updates the
        corresponding data if it is one of the following types:
        StatusData, LogsData, BackupData or AppData.
        If any other type is provided as an argument to this function,
        a SquareException will be raised.

        :param args: Pass a variable number of arguments to a function
        :return: None
        """
        for arg in args:
            if isinstance(arg, StatusData):
                self._status = arg
            elif isinstance(arg, LogsData):
                self._logs = arg
            elif isinstance(arg, BackupData):
                self._backup = arg
            elif isinstance(arg, AppData):
                self._app_data = arg
            else:
                types: list = [
                    i.__name__
                    for i in [
                        StatusData,
                        LogsData,
                        BackupData,
                        AppData,
                    ]
                ]
                raise errors.SquareException(
                    f'you must provide stats of the following types:\n{types}'
                )


class Application(CaptureListenerManager):
    """Represents an application"""

    __slots__ = [
        '_client',
        '_http',
        '_listener',
        '_data',
        'cache',
        '_id',
        '_name',
        '_desc',
        '_domain',
        '_custom',
        '_ram',
        '_lang',
        '_cluster',
        'always_avoid_listeners',
    ]

    def __init__(
        self,
        client: 'Client',
        http: HTTPClient,
        id: str,
        name: str,
        ram: PositiveInt,
        lang: str,
        cluster: str,
        domain: str | None,
        custom: str | None,
        desc: str | None = None,
    ) -> None:
        """
        The `__init__` method is called when the class is instantiated.
        It sets up all the attributes that are passed in as arguments,
        and does any other initialization your class needs before It's ready
        for use.


        :param client: Store a reference to the client that created
        this app.
        :param http: Store a reference to the HTTPClient
        :param id: The application id
        :param name: The tag of the app
        :param ram: The amount of ram that is allocated
        :param lang: The programming language of the app
        :param cluster: The cluster that the app is hosted on
        :param desc: Define the description of the app
        :param domain: Define the domain of the app
        :param custom: Define the custom domain of the app

        :return: None
        """
        self._id: str = id
        self._name: str = name
        self._domain: str | None = domain
        self._custom: str | None = custom
        self._desc: str | None = desc
        self._ram: PositiveInt = ram
        self._lang: str = lang
        self._cluster: str = cluster
        self._client: 'Client' = client
        self._http: HTTPClient = http
        self._listener: CaptureListenerManager = CaptureListenerManager()
        self.cache: AppCache = AppCache()
        self.always_avoid_listeners: bool = False
        super().__init__()

    def __repr__(self) -> str:
        """
        The `__repr__` method is used to create a string representation of an
        object.
        This is useful for debugging, logging and other instances where you
        would want a string representation of the object.
        The __repr__ function should return a string that would make sense to
        someone looking at the results in the interactive interpreter.

        :return: The class name, tag and id of the element
        :rtype: str
        """
        return f'<{self.__class__.__name__} tag={self.name} id={self.id}>'

    @property
    def client(self) -> 'Client':
        """
        The client method is a property that returns the client object.

        :return: The client instance
        :rtype: Client
        """
        return self._client

    @property
    def id(self) -> str:
        """
        The id function is a property that returns
        the id of the application.

        :return: The id of the application
        :rtype: str
        """
        return self._id

    @property
    def name(self) -> str:
        """
        The tag function is a property that returns the application tag.

        :return: The tag of the application
        :rtype: str
        """
        return self._name

    @property
    def desc(self) -> str | None:
        """
        The desc function is a property that returns the description of
        the application.

        :return: The description of the application
        :rtype: str | None
        """
        return self._desc

    @property
    def ram(self) -> int:
        """
        The ram function is a property that returns
        the amount of ram allocated to the application

        :return: The application ram
        :rtype: PositiveInt
        """
        return self._ram

    @property
    def lang(self) -> str:
        """
        The lang function is a property that returns the application's
        programing language.

        :return: The application's programing language
        :rtype: str
        """
        return self._lang

    @property
    def cluster(self) -> str:
        """
        The cluster function is a property that returns the
        cluster that the application is
        running on.


        :return: The cluster that the application is running
        :rtype: str
        """
        return self._cluster

    @property
    def domain(self) -> str | None:
        """
        The domain function is a property that returns the
        application's domain.


        :return: The application's domain
        :rtype: str | None
        """
        return self._domain

    @property
    def custom(self) -> str | None:
        """
        The custom function is a property that returns the
        application's custom domain.


        :return: The application's domain
        :rtype: str | None
        """
        return self._custom

    @staticmethod
    def _notify_listener(endpoint: Endpoint):
        """
        The _notify_listener function is a decorator that call a listener after
        the decorated coroutine is called

        :param endpoint: the endpoint for witch the listener will fetch
        :return: a callable
        """

        def wrapper(func: Callable):
            @wraps(func)
            async def decorator(self: Application, *args, **kwargs) -> Any:
                result = await func(self, *args, **kwargs)
                avoid_listener = kwargs.pop('avoid_listener', False)
                if not (avoid_listener or self.always_avoid_listeners):
                    await self.notify(
                        endpoint=endpoint,
                        before=self.cache.app_data,
                        after=result,
                        extra=kwargs.get('extra'),
                    )
                return result

            return decorator

        return wrapper

    @staticmethod
    def _update_cache(func: Callable):
        """
        This is a decorator checks whether the kwargs `update_cache` in the
        decorated coroutine is not False, and updates the application cache

        :param func:
        :return: a callable
        """

        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            update_cache = kwargs.pop('update_cache', True)
            result = await func(self, *args, **kwargs)
            if update_cache:
                self.cache.update(result)
            return result

        return wrapper

    def capture(self, endpoint: Endpoint, **kwargs) -> Callable:
        """
        The capture function is a decorator that can be used to add a callable
        to be called when a request is made to the specified endpoint.

        :param self: Refer to the class instance.
        :param endpoint: Endpoint: Specify which endpoint the function will be
        called on
        :return: A decorator
        :rtype: Callable
        """

        def wrapper(
            call: Callable[[Endpoint, Endpoint], Any]
        ) -> Callable[[Endpoint, Endpoint], Any]:
            """
            The wrapper function is a decorator that takes in the endpoint as
            an argument.
            It then checks if the endpoint is allowed, and if it isn't, raises
            a SquareException.
            If there's no capture_listener for that endpoint yet, it adds one
            with the function passed to wrapper().
            Otherwise, it raises another SquareException.

            :param call: Pass the function to be wrapped
            :return: The wrapper function itself
            :rtype: None
            :raises InvalidListener: Raised if the endpoint is already
            registered
            """
            for key, value in kwargs.items():
                if key not in ListenerConfig.__annotations__:
                    raise ValueError(
                        f'Invalid listener configuration: "{key}={value}"'
                    )
            config = ListenerConfig(**kwargs)
            listener = Listener(
                app=self,
                client=self.client,
                endpoint=endpoint,
                callback=call,
                config=config,
            )
            self.include_listener(listener)
            return call

        return wrapper

    @_update_cache
    @_notify_listener(Endpoint.app_data())
    async def data(self, *_args, **__kwargs) -> AppData:
        """
        The data method is used to retrieve the data of this app.

        :param self: Refer to the class instance
        :return: A AppData object
        :rtype: AppData
        """
        app_data: AppData = await self.client.app_data(self.id)
        return app_data

    @_update_cache
    @_notify_listener(Endpoint.logs())
    async def logs(self, *_args, **__kwargs) -> LogsData:
        """
        The logs method is used to get the application's logs.

        :param self: Refer to the class instance
        :return: A LogsData object
        :rtype: LogsData
        """
        logs: LogsData = await self.client.get_logs(self.id)
        return logs

    @_update_cache
    @_notify_listener(Endpoint.app_status())
    async def status(self, *_args, **__kwargs) -> StatusData:
        """
        The status function returns the status of an application.

        :param self: Refer to the class instance
        :return: A StatusData object
        :rtype: StatusData
        """
        status: StatusData = await self.client.app_status(self.id)
        return status

    @_update_cache
    @_notify_listener(Endpoint.backup())
    async def backup(self, *_args, **__kwargs) -> BackupData:
        """
        The backup function is used to create a backup of the application.

        :param self: Refer to the class instance
        :return: A BackupData object
        :rtype: BackupData
        """
        backup: BackupData = await self.client.backup(self.id)
        return backup

    async def start(self) -> Response:
        """
        The start function starts the application.

        :param self: Refer to the class instance
        :return: A Response object
        :rtype: Response
        """
        response: Response = await self.client.start_app(
            self.id, avoid_listener=True
        )
        return response

    async def stop(self) -> Response:
        """
        The stop function stops the application.

        :param self: Refer to the class instance
        :return: A Response object
        :rtype: Response
        """
        response: Response = await self.client.stop_app(
            self.id, avoid_listener=True
        )
        return response

    async def restart(self) -> Response:
        """
        The restart function restarts the application.

        :param self: Refer to the class instance
        :return: The Response object
        :rtype: Response
        """
        response: Response = await self.client.restart_app(
            self.id, avoid_listener=True
        )
        return response

    async def delete(self) -> Response:
        """
        The delete function deletes the application.

        :param self: Refer to the class instance
        :return: A Response object
        :rtype: Response
        """
        response: Response = await self.client.delete_app(
            self.id, avoid_listener=True
        )
        return response

    async def commit(self, file: File) -> Response:
        """
        The commit function is used to commit the application.


        :param self: Refer to the class instance
        :param file: File: The squarecloud.File to be committed
        :return: A Response object
        :rtype: Response
        """
        response: Response = await self.client.commit(
            self.id, file=file, avoid_listener=True
        )
        return response

    async def files_list(self, path: str) -> list[FileInfo]:
        """
        The files_list function returns a list of files and folders in the
        specified directory.

        :param self: Refer to the class instance
        :param path: str: Specify the path of the file to be listed
        :return: A list of FileInfo objects.
        :rtype: list[FileInfo]
        """
        response: list[FileInfo] = await self.client.app_files_list(
            self.id,
            path,
            avoid_listener=True,
        )
        return response

    async def read_file(self, path: str) -> BytesIO:
        """
        The read_file function reads the contents of a file from an app.

        :param self: Refer to the class instance
        :param path: str: Specify the path of the file to be read
        :return: A BytesIO object
        :rtype: BytesIO
        """
        response: BytesIO = await self.client.read_app_file(
            self.id, path, avoid_listener=True
        )
        return response

    async def create_file(self, file: File, path: str) -> Response:

        """
        The create_file function creates a file in the specified path.

        :param self: Refer to the class instance
        :param file: File: Specify the file that is to be uploaded
        :param path: str: Specify the path of the file to be created
        :return: A Response object
        :rtype: Response
        """
        response: Response = await self.client.create_app_file(
            self.id,
            file,
            path,
            avoid_listener=True,
        )
        return response

    async def delete_file(self, path: str) -> Response:
        """
        The delete_file function deletes a file from the app.

        :param self: Refer to the class instance
        :param path: str: Specify the path of the file to be deleted
        :return: A Response object
        :rtype: Response
        """
        response: Response = await self.client.delete_app_file(
            self.id, path, avoid_listener=True
        )
        return response

    async def last_deploys(self) -> list[list[DeployData]]:
        """
        The last_deploys function returns a list of the last deploys for this
        application.

        :param self: Represent the instance of the class
        :param: Pass in keyword arguments as a dictionary
        :return: A list of DeployData objects
        """
        response: list[list[DeployData]] = await self.client.last_deploys(
            self.id,
            avoid_listener=True,
        )
        return response

    async def github_integration(self, access_token: str) -> str:
        """
        The create_github_integration function returns a webhook to integrate
        with a GitHub repository.

        :param self: Access the properties of the class
        :param access_token: str: Authenticate the user with GitHub
        :return: A string containing the webhook url
        """
        webhook: str = await self.client.github_integration(
            self.id,
            access_token,
            avoid_listener=True,
        )
        return webhook

    async def domain_analytics(self) -> DomainAnalytics:
        analytics: DomainAnalytics = await self.client.domain_analytics(
            self.id, avoid_listener=True
        )
        return analytics

    async def set_custom_domain(self, custom_domain: str):
        response: Response = await self.client.set_custom_domain(
            self.id, custom_domain, avoid_listener=True
        )
        return response
