"""This module is a wrapper for using the SquareCloud API"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any, Callable, List, Literal

from . import File
from .app import Application
from .data import (
    AppData,
    BackupData,
    FileInfo,
    LogsData,
    StatisticsData,
    StatusData,
    UploadData,
    UserData,
)
from .errors import ApplicationNotFound, InvalidFile, SquareException
from .http import HTTPClient, Response
from .http.endpoints import Endpoint
from .listener import Listener, ListenerManager
from .logs import logger
from .payloads import (
    BackupPayload,
    LogsPayload,
    StatusPayload,
    UploadPayload,
    UserPayload,
)


class AbstractClient(ABC):
    """Abstract client class"""

    @property
    @abstractmethod
    def api_key(self):
        """get the api token"""


def create_config_file(
    path: str,
    display_name: str,
    main: str,
    memory: int,
    version: Literal['recommended', 'latest'] = 'recommended',
    avatar: str | None = None,
    description: str | None = None,
    subdomain: str | None = None,
    start: str | None = None,
    auto_restart: bool | None = None,
):
    """
    The create_config_file function creates a squarecloud.app file in the
    specified path, with the given parameters.
    The function takes in 8 arguments:

    :param path: str: Specify the path to the folder where you want to create
    your config file
    :param display_name: str: Set the display name of your app
    :param main: str: Specify the file that will be executed when the app
    is started
    :param memory: int: Set the memory of the app
    :param version: Literal['recommended', 'latest']: Ensure that the version
    is either 'recommended' or 'latest'.
    :param avatar: str | None: Specify the avatar of the application
    :param description: str | None: Specify a description for the app
    :param subdomain: str | None: Specify the subdomain of your app
    :param start: str | None: Specify the command that should be run when the
    application starts
    :param auto_restart: bool | None: Determine if the app should restart
    automatically after a crash
    :param : Specify the path to the directory where you want to create a
    configuration file
    :return: A File object
    :doc-author: Trelent
    """
    content: str = ''
    optionals: dict[str, Any] = {
        'DISPLAY_NAME': display_name,
        'MAIN': main,
        'MEMORY': memory,
        'VERSION': version,
        'AVATAR': avatar,
        'DESCRIPTION': description,
        'SUBDOMAIN': subdomain,
        'START': start,
        'AUTORESTART': auto_restart,
    }
    for key, value in optionals.items():
        if value is not None:
            string: str = f'{key}={value}\n'
            content += string
    with open(f'./{path}/squarecloud.app', 'w', encoding='utf-8') as file:
        file.write(content)
        return file


class Client(AbstractClient):
    """A client for interacting with the SquareCloud API."""

    def __init__(self, api_key: str, debug: bool = True) -> None:

        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and defines all of its
        attributes.


        :param self: Refer to the instance of the class
        :param api_key: str: Your API key, get in:
         https://squarecloud.app/dashboard/me
        :param debug: bool: Set the logging level to debug
        :return: None
        """
        self.debug = debug
        self._api_key = api_key
        self._http = HTTPClient(api_key=api_key)
        self._listener: ListenerManager = Listener
        if self.debug:
            logger.setLevel(logging.DEBUG)

    @property
    def api_key(self) -> str:
        """
        The api_key function returns the api key for the client.

        :param self: Refer to the instance of the class
        :return: The api key
        """
        return self._api_key

    def on_request(self, endpoint: Endpoint):
        """
        The on_request function is a decorator that allows you to register a
        function as an endpoint listener.

        :param self: Refer to the instance of the class
        :param endpoint: Endpoint: Specify the endpoint that will be used to
        capture the request
        :return: A wrapper function
        """

        def wrapper(func: Callable):
            """
            The wrapper function is a decorator that wraps the function passed
            to it.
            It takes in a function, and returns another function. The wrapper
            will call
            the wrapped function with all of its arguments, and then do
            something extra
            with the result.

            :param func: Callable: Specify the type of the parameter
            :return: The function itself, if the endpoint is not already
            registered
            """
            if not self._listener.get_request_listener(endpoint):
                return self._listener.add_request_listener(endpoint, func)
            raise SquareException(
                f'Already exists an capture_listener for {endpoint}'
            )

        return wrapper

    async def me(self, **kwargs) -> UserData:
        """
        This function is used to get your information.

        :param self: Refer to the instance of the class
        :param kwargs: Pass in a dictionary of arguments
        :return: A userdata object
        """
        response: Response = await self._http.fetch_user_info()
        payload: UserPayload = response.response
        user_data: UserData = UserData(**payload['user'])
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return user_data

    async def user_info(
        self, user_id: int | None = None, **kwargs
    ) -> UserData:
        """
        The user_info function is used to get information about a user.

        :param self: Refer to the instance of the class
        :param user_id: int | None: Specify the user id of the user you want
        to get information about
        :param kwargs: Pass in keyword arguments to a function
        :return: A UserData object
        """
        response: Response = await self._http.fetch_user_info(user_id=user_id)
        payload: UserPayload = response.response
        user_data: UserData = UserData(**payload['user'])
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return user_data

    async def get_logs(self, app_id: str, **kwargs) -> LogsData:
        """
        The get_logs function is used to get logs for an application.

        :param self: Refer to the instance of the class
        :param app_id: str: Identify the application id
        :param kwargs: Pass in any additional parameters that may be required
        for the function to work
        :return: A LogsData object, which is a named tuple
        """
        response: Response | None = await self._http.fetch_logs(app_id)
        if not response:
            return LogsData(logs=None)
        payload: LogsPayload = response.response
        logs_data: LogsData = LogsData(**payload)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return logs_data

    async def app_status(self, app_id: str, **kwargs) -> StatusData:
        """
        The app_status function is used to get the status of an application.

        :param self: Refer to the instance of the class
        :param app_id: str: Specify the application id
        :param kwargs: Pass in keyword arguments to a function
        :return: A StatusData object
        """
        response: Response = await self._http.fetch_app_status(app_id)
        payload: StatusPayload = response.response
        status: StatusData = StatusData(**payload)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return status

    async def start_app(self, app_id: str, **kwargs) -> Response:
        """
        The start_app function starts an application.

        :param self: Refer to the instance of the class
        :param app_id: str: Identify the application to start
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A Response object
        """
        response: Response = await self._http.start_application(app_id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return response

    async def stop_app(self, app_id: str, **kwargs) -> Response:
        """
        The stop_app function stops an application.

        :param self: Refer to the instance of the class
        :param app_id: str: Specify the application id
        :param kwargs: Pass in keyword arguments to the function
        :return: A Response object
        """
        response: Response = await self._http.stop_application(app_id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return response

    async def restart_app(self, app_id: str, **kwargs) -> Response:
        """
        The restart_app function is used to restart an application.

        :param self: Refer to the instance of the class
        :param app_id: str: Specify the application id
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A Response object
        """
        response: Response = await self._http.restart_application(app_id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return response

    async def backup(self, app_id: str, **kwargs) -> BackupData:
        """
        The backup function is used to backup an application.

        :param self: Refer to the instance of the class
        :param app_id: str: Identify the application to be backed up
        :param kwargs: Pass in additional parameters to the function
        :return: A BackupData object
        """
        response: Response = await self._http.backup(app_id)
        payload: BackupPayload = response.response
        backup: BackupData = BackupData(**payload)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return backup

    async def delete_app(self, app_id: str, **kwargs) -> Response:
        """
        The delete_app function deletes an application.

        :param self: Refer to the instance of the class
        :param app_id: str: Specify the application id
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A Response object
        """
        response: Response = await self._http.delete_application(app_id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return response

    async def commit(self, app_id: str, file: File, **kwargs) -> Response:
        """
        The commit function is used to commit an application.

        :param self: Bind the method commit to an object
        :param app_id: str: Identify the application
        :param file: File: Specify the file object to be committed
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A response object
        """
        response: Response = await self._http.commit(app_id, file)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return response

    async def app(self, app_id: str, **kwargs) -> Application:
        """
        The app function is used to get an application.

        :param self: Refer to the instance of the class
        :param app_id: str: The application id
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: An application object
        """
        response: Response = await self._http.fetch_user_info()
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        payload: UserPayload = response.response
        app_data = list(
            filter(
                lambda application: application['id'] == app_id,
                payload['applications'],
            )
        )
        if not app_data:
            raise ApplicationNotFound
        app_data = app_data.pop()
        app: Application = Application(
            client=self, http=self._http, **app_data
        )  # type: ignore
        return app

    async def all_apps(self, **kwargs) -> List[Application]:
        """
        The all_apps function returns a list of all applications that the user
        has access to.

        :param self: Refer to the instance of the class
        :param kwargs: Pass in the avoid_listener parameter
        :return: A list of Application objects
        """
        response: Response = await self._http.fetch_user_info()
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        payload: UserPayload = response.response
        apps_data: list = payload['applications']
        apps: List[Application] = [
            Application(client=self, http=self._http, **data)
            for data in apps_data
        ]
        return apps

    async def upload_app(self, file: File, **kwargs) -> UploadData:
        """
        The upload_app function uploads an application to the server.

        :param self: Refer to the instance of the class
        :param file: File: Upload a file
        :param kwargs: Pass a variable number of keyword arguments to a
        function
        :return: An UploadData object, which is a class that contains the data
        of the application uploaded
        """
        if not isinstance(file, File):
            raise InvalidFile(f'you need provide an {File.__name__} object')

        # Se for io.BytesIO o file.filename é nulo.
        if (file.filename is not None) and (
            file.filename.split('.')[-1] != 'zip'
        ):
            raise InvalidFile('the file must be a .zip file')
        response: Response = await self._http.upload(file)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        payload: UploadPayload = response.response.get('app')
        app: UploadData = UploadData(**payload)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return app

    async def app_files_list(
        self, app_id: str, path: str, **kwargs
    ) -> list[FileInfo] | None:
        """
        The app_files_list function returns a list of your application files.

        :param self: Refer to the instance of the class
        :param app_id: str: Identify the application id
        :param path: str: Specify the path to the file
        :param kwargs: Pass a variable number of keyword arguments to a
        function
        :return: A list of your Application files
        """
        response: Response = await self._http.fetch_app_files_list(
            app_id, path
        )
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )

        if not response.response[0]:  # type ignore
            return
        return [FileInfo(**data) for data in response.response]

    async def read_app_file(self, app_id: str, path: str, **kwargs) -> BytesIO:
        """
        The read_app_file function reads a file from the specified path and
        returns a BytesIO representation.

        :param self: Refer to the instance of the class
        :param app_id: str: Specify the application id
        :param path: str: Specify the path of the file to be read
        :param kwargs: Pass in additional arguments to the function
        :return: A BytesIO representation of the file
        :doc-author: Trelent
        """
        response: Response = await self._http.read_app_file(app_id, path)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        if response.response:
            return BytesIO(bytes(response.response.get('data')))

    async def create_app_file(
        self, app_id: str, file: File, path: str, **kwargs
    ) -> Response:
        """ ""
        The create_app_file function creates a new file in the specified
        directory.

        :param self: Refer to the instance of the class
        :param app_id: str: Specify the application id
        :param file: File: Pass the file to be created
        :param path: str: Specify the directory to create the file in
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A Response object
        """
        if not isinstance(file, File):
            raise SquareException(
                'the file must be an string or a squarecloud.File object'
            )
        file_bytes = list(file.bytes.read())
        response: Response = await self._http.create_app_file(
            app_id, file_bytes, path
        )
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        file.bytes.close()

        return response

    async def delete_app_file(
        self, app_id: str, path: str, **kwargs
    ) -> Response:
        """ "
        The delete_app_file function deletes a file in the specified directory.

        :param self: Refer to the instance of the class
        :param app_id: str: Specify the application id
        :param path: str: Specify the directory where the file should be
        deleted
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: A Response object
        """
        response: Response = await self._http.file_delete(app_id, path)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return response

    async def statistics(self, **kwargs) -> StatisticsData:
        """
        The statistics function returns a StatisticsData object

        :param self: Represent the instance of a class
        :param kwargs: Pass in a dictionary of parameters
        :return: A StatisticsData object, which is a class that contains all
        the data returned by the endpoint
        """
        response: Response = await self._http.get_statistics()
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        data = response.response['statistics']
        return StatisticsData(**data)

    async def app_data(self, app_id: str, **kwargs) -> AppData:
        """ "
        The app_data function is used to get application data.

        :param self: Refer to the instance of the class
        :param app_id: str: The application id
        :param kwargs: Pass a variable number of keyword arguments to the
        function
        :return: An AppData object
        """
        response: Response = await self._http.get_app_data(app_id)
        if not kwargs.get('avoid_listener'):
            endpoint: Endpoint = response.route.endpoint
            await self._listener.on_request(
                endpoint=endpoint, response=response
            )
        return AppData(**response.response.get('app'))
