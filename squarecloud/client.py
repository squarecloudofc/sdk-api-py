"""This module is a wrapper for using the SquareCloud API"""
from __future__ import annotations

import logging
from typing import List
from abc import ABC, abstractmethod

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


class AbstractClient(ABC):
    """Abstract client class"""

    @property
    @abstractmethod
    def api_key(self):
        """get the api token"""


class Client(AbstractClient):
    """A client for interacting with the SquareCloud API."""

    def __init__(self, api_key: str, debug: bool = True) -> None:
        self.debug = debug
        self._api_key = api_key
        self.__http = HTTPClient(api_key=api_key)
        if self.debug:
            logger.setLevel(logging.DEBUG)

    @property
    def api_key(self):
        """
        The SquareCloud API key.

        Returns:
            self.__api_key
        """
        return self._api_key

    async def user_info(self):
        """
        Get your information

        Returns:
            UserData
        """
        result: Response = await self.__http.fetch_user_info()
        if result.status == 200:
            payload: UserPayload = result.response
            user_data: UserData = UserData(**payload['user'])
            return user_data
        return

    async def get_logs(self, app_id: int | str):
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

    async def logs_complete(self, app_id: int | str):
        """
        Get logs for an application'

        Args:
            app_id:

        Returns:
            CompleteLogsData
        """
        result: Response = await self.__http.fetch_logs_complete(app_id)
        payload: CompleteLogsPayload = result.response
        logs_data: CompleteLogsData = CompleteLogsData(**payload)
        return logs_data

    async def app_status(self, app_id: int | str):
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

    async def start_app(self, app_id: int | str):
        """
        Start an application

        Args:
            app_id: the application ID
        """
        await self.__http.start_application(app_id)

    async def stop_app(self, app_id: int | str):
        """
        Stop an application

        Args:
            app_id: the application ID
        """
        await self.__http.stop_application(app_id)

    async def restart_app(self, app_id: int | str):
        """
        Restart an application

        Args:
            app_id: the application ID
        """
        await self.__http.restart_application(app_id)

    async def backup(self, app_id: int | str):
        """
        Backup an application

        Args:
            app_id: the application ID
        Returns:
            BackupPayload
        """
        result: Response = await self.__http.backup(app_id)
        payload: BackupPayload = result.data.get('response')
        backup: BackupData = BackupData(**payload)
        return backup

    async def delete_app(self, app_id: int | str):
        """
        D
        Args:
            app_id:

        Returns:

        """
        await self.__http.delete_application(app_id)

    async def commit(self, app_id: int | str, file: File):
        """
        Commit an application

        Args:
            app_id: the application ID
            file: the file object to be committed
        """
        await self.__http.commit(app_id, file)

    async def fetch_apps(self):
        """
        Get a list of your applications

        Returns:
            List[AppData]
        """
        result: Response = await self.__http.fetch_user_info()
        payload: list = result.data['response']['applications']
        apps_data: List[AppData] = [AppData(**app_data) for app_data in payload]
        apps: List[Application] = [Application(client=self, data=data) for data in apps_data]
        return apps
