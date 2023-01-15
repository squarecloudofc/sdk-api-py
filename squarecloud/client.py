"""This module is a wrapper for using the SquareCloud API"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Literal, Any, Callable

from .app import Application
from .data import (
    AppData,
    StatusData,
    UserData,
    LogsData,
    BackupData,
    FullLogsData,
    UploadData
)
from .errors import ApplicationNotFound, InvalidFile, SquareException
from .http import HTTPClient, Response
from .http.endpoints import Endpoint
from .listener import ListenerManager, Listener
from .logs import logger
from .payloads import (
    UserPayload,
    StatusPayload,
    LogsPayload,
    BackupPayload,
    FullLogsPayload,
    UploadPayload,
)
from .square import File


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
        version: Literal['recommended', 'latest'],
        avatar: str | None = None,
        description: str | None = None,
        subdomain: str | None = None,
        start: str | None = None
):
    """
    Creates a config file (squarecloud.app)
    Args:

        display_name: name of your application
        main: name of your main file
        memory: amount of memory to be allocated
        version: version of python and node.js, you can choose between
        'recommended' and 'latest'
        avatar: your application avatar url
        description: your application description
        subdomain: subdomain of your application
        start: the command to start your application
        path: the path where the file should be saved

    Returns:
        TextIOWrapper
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
        """With this class you can manage/get information from
        your applications

        Args:
            api_key:Your API key, get in https://squarecloud.app/dashboard/me
            debug: if True logs are generated with information about requests
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
        Get client api key

        Returns:
            self.__api_key
        """
        return self._api_key

    def on_request(self, endpoint: Endpoint):
        def wrapper(func: Callable):
            if not self._listener.get_request_listener(endpoint):
                return self._listener.add_request_listener(endpoint, func)
            raise SquareException(
                f'Already exists an capture_listener for {endpoint}')

        return wrapper

    async def me(self) -> UserData:
        response: Response = await self._http.fetch_user_info()
        payload: UserPayload = response.response
        user_data: UserData = UserData(**payload['user'])
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return user_data

    async def user_info(self, user_id: int | None = None) -> UserData:
        """
        Get user information

        Returns:
            UserData
        """
        response: Response = await self._http.fetch_user_info(user_id=user_id)
        payload: UserPayload = response.response
        user_data: UserData = UserData(**payload['user'])
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return user_data

    async def get_logs(self, app_id: str) -> LogsData:
        """
        Get logs for an application

        Args:
            app_id: the application ID

        Returns:
            LogData
        """
        response: Response = await self._http.fetch_logs(app_id)
        payload: LogsPayload = response.response
        logs_data: LogsData = LogsData(**payload)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return logs_data

    async def full_logs(self, app_id: str) -> FullLogsData:
        """
        Get logs for an application'

        Args:
            app_id: the application ID

        Returns:
            FullLogsData
        """
        response: Response = await self._http.fetch_logs_complete(app_id)
        payload: FullLogsPayload = response.response
        logs_data: FullLogsData = FullLogsData(**payload)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return logs_data

    async def app_status(self, app_id: str) -> StatusData:
        """
        Get an application status

        Args:
            app_id: the application ID

        Returns:
            StatusData
        """
        response: Response = await self._http.fetch_app_status(app_id)
        payload: StatusPayload = response.response
        status: StatusData = StatusData(**payload)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return status

    async def start_app(self, app_id: str) -> Response:
        """
        Start an application

        Args:
            app_id: the application ID
        """

        response: Response = await self._http.start_application(app_id)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return response

    async def stop_app(self, app_id: str) -> Response:
        """
        Stop an application

        Args:
            app_id: the application ID
        """
        response: Response = await self._http.stop_application(app_id)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return response

    async def restart_app(self, app_id: str) -> Response:
        """
        Restart an application

        Args:
            app_id: the application ID
        """
        response: Response = await self._http.restart_application(app_id)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return response

    async def backup(self, app_id: str) -> BackupData:
        """
        Backup an application

        Args:
            app_id: the application ID
        Returns:
            Backup
        """
        response: Response = await self._http.backup(app_id)
        payload: BackupPayload = response.response
        backup: BackupData = BackupData(**payload)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return backup

    async def delete_app(self, app_id: str) -> Response:
        """
        Delete an application

        Args:
            app_id: the application ID
        """
        response: Response = await self._http.delete_application(app_id)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return response

    async def commit(self, app_id: str, file: File) -> Response:
        """
        Commit an application

        Args:
            app_id: the application ID
            file: the file object to be committed
        """
        response: Response = await self._http.commit(app_id, file)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return response

    async def app(self, app_id: str) -> Application:
        """
        Get an application

        Args:
            app_id: the application ID
        """
        response: Response = await self._http.fetch_user_info()
        payload: UserPayload = response.response
        app_data = list(filter(lambda application: application['id'] == app_id,
                               payload['applications']))
        if not app_data:
            raise ApplicationNotFound
        app_data = app_data.pop()
        app: Application = Application(
            client=self, http=self._http,
            data=AppData(**app_data))  # type: ignore
        return app

    async def all_apps(self) -> List[Application]:
        """
        Get a list of your applications

        Returns:
            List[AppData]
        """
        response: Response = await self._http.fetch_user_info()
        payload: UserPayload = response.response
        apps_data: List[AppData] = [
            AppData(**app_data) for app_data in  # type: ignore
            payload['applications']]
        apps: List[Application] = [
            Application(client=self, http=self._http, data=data) for data
            in apps_data]
        return apps

    async def upload_app(self, file: File) -> UploadData:
        if not isinstance(file, File):
            raise InvalidFile(
                f'you need provide an {File.__name__} object')
        if file.name.split('.')[-1] != 'zip':
            raise InvalidFile('the file must be a .zip file')
        response: Response = await self._http.upload(file)
        payload: UploadPayload = response.app
        app: UploadData = UploadData(**payload)
        endpoint: Endpoint = response.route.endpoint
        await self._listener.on_request(endpoint=endpoint, response=response)
        return app
