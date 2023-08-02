import logging
from abc import ABC
from io import BytesIO
from typing import TYPE_CHECKING, Callable, Literal

from .data import AppData, BackupData, FileInfo, LogsData, StatusData
from .errors import SquareException
from .file import File
from .http import Endpoint, HTTPClient, Response
from .listener import Listener, ListenerManager

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
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and defines all of its attributes.


        :param self: Represent the instance of the class
        :return: The instance of the class
        """
        self.status: StatusData | None = None
        self.logs: LogsData | None = None
        self.backup: BackupData | None = None
        self.data: AppData | None = None

    def clear(self):
        """
        The clear function is used to clear the status, logs, backup and data
        variables.

        :param self: Represent the instance of the class
        :return: None
        """
        self.status = None
        self.logs = None
        self.backup = None
        self.data = None

    def update(self, *args):
        """
        The update function is used to update the data of a given instance.
        It takes in an arbitrary number of arguments, and updates the
        corresponding data if it is one of the following types:
        StatusData, LogsData, BackupData or AppData.
        If any other type is provided as an argument to this function,
        a SquareException will be raised.

        :param self: Represent the instance of the class
        :param args: Pass a variable number of arguments to a function
        :return: None
        """
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
                    i.__name__
                    for i in [
                        StatusData,
                        LogsData,
                        BackupData,
                        AppData,
                    ]
                ]
                raise SquareException(
                    f'you must provide stats of the following types:\n{types}'
                )


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
        'cache',
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
        cluster: Literal[
            'florida-free-1',
            'fl-haswell-4',
            'fl-haswell-3',
            'fl-haswell-2',
            'fl-haswell-1',
            'fl-vps-1',
        ],
        isWebsite: bool,
        avatar: str,
        desc: str | None = None,
    ):
        """
        The __init__ function is called when the class is instantiated.
        It sets up all the attributes that are passed in as arguments,
        and does any other initialization your class needs before its ready
        for use.


        :param self: Represent the instance of the class
        :param client: 'Client': Store a reference to the client that created
        this app
        :param http: HTTPClient: Make http requests to the api
        :param id: str: Set the id of the app
        :param tag: str: Get the tag of the app
        :param ram: int: Set the amount of ram that is used by the app
        :param lang: Literal[
                        'javascript',
                        'typescript',
                        'python',
                        'java',
                        'rust',
                        'go',
                        'static',
                        'dynamic',
                    ]: Specify the language of the app
        :param type: Literal['free', 'paid] : Determine whether the app is a free or paid app
        :param cluster: Literal[
                'florida-free-1',
                'fl-haswell-4',
                'fl-haswell-3',
                'fl-haswell-2',
                'fl-haswell-1',
                'fl-vps-1',
            ]: Determine the cluster that the app is hosted on
        :param isWebsite: bool: Whether if the app is a website
        :param avatar: str: The app avatar
        :param desc: str | None: Define the description of the app
        :return: None
        """
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
        """
        The __repr__ function is used to create a string representation of an
        object.
        This is useful for debugging, logging and other instances where you
        would want a string representation of the object.
        The __repr__ function should return a string that would make sense to
        someone looking at the results in the interactive interpreter.


        :param self: Refer to the current instance of the class
        :return: The class name, tag and id of the element
        """
        return f'<{self.__class__.__name__} tag={self.tag} id={self.id}>'

    @property
    def client(self):
        """
        The client function returns the client object.

        :param self: Represent the instance of the class
        :return: The client instance
        """
        return self._client

    @property
    def id(self):
        """
        The id function returns the id of a given instance of the class.

        :param self: Represent the instance of the object itself
        :return: The id of the application
        """
        return self._id

    @property
    def tag(self):
        """
        The tag function returns the application tag.

        :param self: Represent the instance of the object itself
        :return: The tag of the application
        """
        return self._tag

    @property
    def desc(self):
        """
        The desc function returns the description of the application.

        :param self: Represent the instance of the class
        :return: The description of the application
        """
        return self._desc

    @property
    def ram(self):

        """
        The ram function returns the amount of ram allocated to the application


        :param self: Refer to the object itself
        :return: The application ram
        :doc-author: Trelent
        """
        return self._ram

    @property
    def lang(self):
        """
        The lang function returns the application's programing language.

        :param self: Represent the instance of the class
        :return: The application's programing language
        """
        return self._lang

    @property
    def type(self):
        """
        The type function returns the application's type.

        :param self: Represent the instance of the object itself
        :return: The application's type
        """
        return self._type

    @property
    def cluster(self):
        """
        The cluster function returns the cluster that the application is
        running on.


        :param self: Represent the instance of the class
        :return: The cluster that the application is assigned to
        """
        return self._cluster

    @property
    def is_website(self):
        """
        The is_website function returns a boolean value indicating whether the
        application is a website.

        :param self: Refer to the object itself
        :return: A boolean value, true or false
        """
        return self._isWebsite

    @property
    def avatar(self):
        """
        The avatar function is a property that returns the avatar of the
        application.

        :param self: Refer to the object itself
        :return: The avatar
        """
        return self._avatar

    def capture(self, endpoint: Endpoint) -> Callable:
        """
        The capture function is a decorator that can be used to add a function
        to be called when a request is made to the specified endpoint.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Specify which endpoint the function will be
        called on
        :return: A decorator
        """
        allowed_endpoints: tuple[Endpoint, Endpoint, Endpoint, Endpoint] = (
            Endpoint.logs(),
            Endpoint.app_status(),
            Endpoint.backup(),
            Endpoint.app_data(),
        )

        def wrapper(func):
            """
            The wrapper function is a decorator that takes in the endpoint as
            an argument.
            It then checks if the endpoint is allowed, and if it isn't, raises
            a SquareException.
            If there's no capture_listener for that endpoint yet, it adds one
            with the function passed to wrapper().
            Otherwise, it raises another SquareException.

            :param func: Pass the function to be wrapped
            :return: The wrapper function itself
            """
            if endpoint not in allowed_endpoints:
                raise SquareException(
                    f'the endpoint to capture must be {allowed_endpoints}'
                )

            if self._listener.get_capture_listener(endpoint) is None:
                return self._listener.add_capture_listener(endpoint, func)
            raise SquareException(
                f'Already exists an capture_listener for {endpoint} {self._listener.get_capture_listener(endpoint)}'
            )

        return wrapper

    async def data(self, **kwargs):
        """
        The data function is used to retrieve the data of an app.

        :param self: Represent the instance of the class
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A AppData object
        """
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
        """
        The logs function is used to get the application's logs.

        :param self: Represent the instance of the class
        :param kwargs: Pass a variable number of keyword arguments to a
        function
        :return: A LogsData object
        """
        logs: LogsData = await self.client.get_logs(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.logs()
            await self._listener.on_capture(
                endpoint=endpoint, before=self.cache.logs, after=logs
            )
        if kwargs.get('update_cache', True):
            self.cache.update(logs)
        return logs

    async def status(self, **kwargs) -> StatusData:
        """
        The status function returns the status of an application.

        :param self: Refer to the object itself
        :param kwargs: Pass a variable number of keyword arguments to a
        function
        :return: A StatusData object
        """
        status: StatusData = await self.client.app_status(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.app_status()
            await self._listener.on_capture(
                endpoint=endpoint, before=self.cache.status, after=status
            )
        if kwargs.get('update_cache', True):
            self.cache.update(status)
        return status

    async def backup(self, **kwargs) -> BackupData:
        """
        The backup function is used to create a backup of the application.

        :param self: Refer to the current instance of the class
        :param kwargs: Pass a variable number of keyword arguments to a
        function
        :return: A BackupData object
        """
        backup: BackupData = await self.client.backup(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.backup()
            await self._listener.on_capture(
                endpoint=endpoint, before=self.cache.backup, after=backup
            )
        if kwargs.get('update_cache', True):
            self.cache.update(backup)
        return backup

    async def start(self, **kwargs) -> Response:
        """
        The start function starts the application.

        :param self: Refer to the instance of the class
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A Response object
        """
        response: Response = await self.client.start_app(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.start()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response

    async def stop(self, **kwargs) -> Response:
        """
        The stop function stops the application.

        :param self: Refer to the current instance of a class
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A Response object
        """
        response: Response = await self.client.stop_app(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.stop()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response

    async def restart(self, **kwargs) -> Response:
        """
        The restart function restarts the application.

        :param self: Refer to the current instance of a class
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: The Response object
        """
        response: Response = await self.client.restart_app(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.restart()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response

    async def delete(self, **kwargs) -> Response:
        """
        The delete function deletes the application.

        :param self: Represent the instance of the class
        :param kwargs: Pass in keyword arguments as a dictionary
        :return: A Response object
        """
        response: Response = await self.client.delete_app(self.id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.delete_app()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response

    async def commit(self, file: File, **kwargs) -> Response:
        """
        The commit function is used to commit the application.


        :param self: Refer to the current object
        :param file: File: Upload the file to be committed
        :param kwargs: Pass a variable number of keyword arguments to the
         function
        :return: A Response object
        """
        response: Response = await self.client.commit(self.id, file=file)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.commit()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response

    async def files_list(self, path: str, **kwargs) -> list[FileInfo]:
        """
        The files_list function returns a list of files and folders in the
        specified directory.

        :param self: Make the function a method of the class
        :param path: str: Specify the path of the file to be listed
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A list of FileInfo objects.
        """
        response: list[FileInfo] = await self.client.app_files_list(
            self.id, path
        )

        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.files_list()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response

    async def read_file(self, path: str, **kwargs) -> BytesIO:
        """
        The read_file function reads the contents of a file from an app.

        :param self: Refer to the object itself
        :param path: str: Specify the path of the file to be read
        :param kwargs: Pass in keyword arguments to the function
        :return: A ButesIO object
        """
        response: BytesIO = await self.client.read_app_file(self.id, path)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.files_read()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response

    async def create_file(self, file: File, path: str, **kwargs) -> Response:

        """
        The create_file function creates a file in the specified path.

        :param self: Refer to the object itself
        :param file: File: Specify the file that is to be uploaded
        :param path: str: Specify the path of the file to be created
        :param kwargs: Pass additional keyword arguments to the function
        :return: A Response object
        """
        response: Response = await self.client.create_app_file(
            self.id, file, path
        )
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.files_read()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response

    async def delete_file(self, path: str, **kwargs) -> Response:
        """
        The delete_file function deletes a file from the app.

        :param self: Refer to the current instance of a class
        :param path: str: Specify the path of the file to be deleted
        :param kwargs: Pass in a dictionary of additional arguments
        :return: A Response object
        """
        response: Response = await self.client.delete_app_file(self.id, path)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = Endpoint.files_delete()
            await self._listener.on_capture(
                endpoint=endpoint, response=response
            )
        return response
