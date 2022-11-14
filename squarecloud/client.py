"""This module is a wrapper for using the SquareCloud API"""
from __future__ import annotations
from threading import Thread
import asyncio
from functools import wraps
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import *

import squarecloud.errors

from .data import (
    AppData,
    StatusData,
    UserData,
    LogsData,
    BackupData,
    CompleteLogsData,
)
from .http import HTTPClient, Response
from .logs import logger
from .square import File, Application
from .types import (
    UserPayload,
    StatusPayload,
    LogsPayload,
    BackupPayload,
    CompleteLogsPayload,
)


# noinspection Pylint
class AbstractClient(ABC):
    """Abstract client class"""

    @property
    @abstractmethod
    def api_key(self):
        """get the api token"""

# noinspection Pylint
class Client(AbstractClient):
    """A client for interacting with the SquareCloud API."""

    def __init__(self, api_key: str, app_ids : list=None, debug: bool = True) -> None:
        """
        :param api_key: Your API key, get in https://squarecloud.app/dashboard/me
        :param app_ids: If default, you will need to specify the app ID in all listeners.
        :param debug:
        """
        self.debug = debug
        self._api_key = api_key
        self.__http = HTTPClient(api_key=api_key)
        self._logs_listener = {}
        self._logs = {}
        self._apps = []
        self._app_ids = app_ids
        self._loop = asyncio.get_event_loop()

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

    @property
    def app_ids(self) -> list:
        """
        Get client intern property app_ids value
        :return: Intern app_ids property
        """
        return [app for app in self._app_ids] if self._apps is not None else None

    async def _set_apps(self) -> list:
        self._apps = [await self.app(app) for app in self._app_ids] if self._app_ids is not None else self._app_ids
        return self._apps

    async def insert_app_id(self, app : str):
        """
        Append app to client intern app_ids list
        :param app: App ID
        """
        if type(app) == str:
            app = await self.app(app)
        self._apps.append(app)
        return True

    async def _process_listeners(self):
        while True:
            for listener in self._logs_listener.keys():
                app = self._logs_listener[listener]['app']
                if self._logs_listener[listener].get('last_check'):
                    last_check = int(str(self._logs_listener[listener]['last_check'])[0:-3])
                    status = await app.status()
                    last_restart = int(str(status.uptime)[0:-3])
                    if last_check < last_restart:
                        self._logs[app.id] = []
                try:
                    logs = await self.get_logs(app_id=app.id)
                except squarecloud.errors.NotFoundError:
                    continue
                logs = logs.logs
                old_logs = self._logs[app.id]
                self._logs[app.id] = logs.split('\n')
                if self._logs_listener[listener]['just_last'] is True:
                    logs = '\n'.join(logs.split('\n')[len(old_logs):len(logs)])

                if logs.replace(' ', '') != '':
                    await self._logs_listener[listener]["func"](logs, app.tag)
                await asyncio.sleep(3)
            await asyncio.sleep(10)

    def capture_logs(self, apps=None, just_last=False):
        """
            A listener to automatically capture and handle logs,
            This functions will consume some requests depending your apps amount.
            - By Mudinho
            Args:
                apps: A list of app IDs - like app_ids client param
                just_last: If True, will be captured just last logs (No repeated logs)
            Returns:
                Logs and App Tag(Name)
        """
        if self._logs_listener == {}:
            self._loop.create_task(self._process_listeners())

        def decorator(func):
            async def wrapped(apps : List[str]=None, just_last : bool=False):

                if apps is None:
                    apps = await self._set_apps()
                else:
                    self._app_ids = apps
                    apps = await self._set_apps()

                for app in apps:
                    if app.id not in self._logs_listener.keys():
                        self._logs_listener[app.id] = {"func" : func, "just_last" : just_last, "app": app}
                        self._logs[app.id] = []
                    else:
                        raise Warning(f'It was not possible to register the logs listener for the application "{app.tag}" - It is already registered in another logs listener')

            self._loop.create_task(wrapped(apps, just_last))

        return decorator


    async def user_info(self) -> UserData:
        """
        Get user information

        Returns:
            UserData
        """
        result: Response = await self.__http.fetch_user_info()
        payload: UserPayload = result.response
        user_data: UserData = UserData(**payload['user'])
        return user_data

    async def get_logs(self, app_id: int | str) -> LogsData:
        """
        Get logs for an application

        Args:
            app_id: the application ID

        Returns:
            LogData
        """
        result: Response = await self.__http.fetch_logs(app_id)
        payload: LogsPayload = result.response
        logs_data: LogsData = LogsData(**payload)
        return logs_data

    async def logs_complete(self, app_id: int | str) -> CompleteLogsData:
        """
        Get logs for an application'

        Args:
            app_id: the application ID

        Returns:
            CompleteLogsData
        """
        result: Response = await self.__http.fetch_logs_complete(app_id)
        payload: CompleteLogsPayload = result.response
        logs_data: CompleteLogsData = CompleteLogsData(**payload)
        return logs_data

    async def app_status(self, app_id: int | str) -> StatusData:
        """
        Get an application status

        Args:
            app_id: the application ID

        Returns:
            StatusData
        """
        result: Response = await self.__http.fetch_app_status(app_id)
        payload: StatusPayload = result.response
        status: StatusData = StatusData(**payload)
        return status

    async def start_app(self, app_id: int | str) -> None:
        """
        Start an application

        Args:
            app_id: the application ID
        """
        await self.__http.start_application(app_id)

    async def stop_app(self, app_id: int | str) -> None:
        """
        Stop an application

        Args:
            app_id: the application ID
        """
        await self.__http.stop_application(app_id)

    async def restart_app(self, app_id: int | str) -> None:
        """
        Restart an application

        Args:
            app_id: the application ID
        """
        await self.__http.restart_application(app_id)

    async def backup(self, app_id: int | str) -> BackupData:
        """
        Backup an application

        Args:
            app_id: the application ID
        Returns:
            Backup
        """
        result: Response = await self.__http.backup(app_id)
        payload: BackupPayload = result.response
        backup: BackupData = BackupData(**payload)
        return backup

    async def delete_app(self, app_id: int | str) -> None:
        """
        Delete an application

        Args:
            app_id: the application ID
        """
        await self.__http.delete_application(app_id)

    async def commit(self, app_id: int | str, file: File) -> None:
        """
        Commit an application

        Args:
            app_id: the application ID
            file: the file object to be committed
        """
        await self.__http.commit(app_id, file)

    async def app(self, app_id: int | str) -> Application:
        """
        Get an application

        Args:
            app_id: the application ID
        """
        result: Response = await self.__http.fetch_user_info()
        payload: UserPayload = result.response
        app_data = list(filter(lambda application: application['id'] == app_id, payload['applications']))[0]
        app: Application = Application(client=self, data=AppData(**app_data))  # type: ignore
        return app

    async def all_apps(self) -> List[Application]:
        """
        Get a list of your applications

        Returns:
            List[AppData]
        """
        result: Response = await self.__http.fetch_user_info()
        payload: UserPayload = result.response
        apps_data: List[AppData] = [AppData(**app_data) for app_data in payload['applications']]  # type: ignore
        apps: List[Application] = [Application(client=self, data=data) for data in apps_data]
        return apps
