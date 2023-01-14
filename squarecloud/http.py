"""Module to manage requests"""
from __future__ import annotations

from typing import Dict, Any

import aiohttp

from .errors import (
    RequestError,
    AuthenticationFailure,
    NotFoundError,
    BadRequestError
)
from .logs import logger
from .square import File
from .types import RawResponseData


class Response:
    """Represents a request response"""

    def __init__(self, data: RawResponseData, route) -> None:
        self.data = data
        self.route = route
        self.headers = data.get('headers')
        self.status = data.get('status')
        self.code = data.get('code')
        self.message = data.get('message')
        self.response = data.get('response')


class Endpoint:
    BASE: str = 'https://api.squarecloud.app/v1/public'
    ENDPOINTS = {
        'USER_INFO': {'METHOD': 'GET', 'PATH': '/user'},
        'APP_STATUS': {'METHOD': 'GET', 'PATH': '/status/{app_id}'},
        'LOGS': {'METHOD': 'GET', 'PATH': '/logs/{app_id}'},
        'FULL_LOGS': {'METHOD': 'GET', 'PATH': '/full-logs/{app_id}'},
        'START': {'METHOD': 'POST', 'PATH': '/start/{app_id}'},
        'STOP': {'METHOD': 'POST', 'PATH': '/stop/{app_id}'},
        'RESTART': {'METHOD': 'POST', 'PATH': '/restart/{app_id}'},
        'BACKUP': {'METHOD': 'GET', 'PATH': '/backup/{app_id}'},
        'COMMIT': {'METHOD': 'POST', 'PATH': '/commit/{app_id}'},
        'DELETE': {'METHOD': 'POST', 'PATH': '/delete/{app_id}'},
        'UPLOAD': {'METHOD': 'POST', 'PATH': '/upload'},
    }

    def __init__(self, name: str):
        endpoint: Dict[str: Dict[str, Any]] = self.ENDPOINTS[name]
        self.name: str = name
        self.method: str = endpoint['METHOD']
        self.path: str = endpoint['PATH']

    def __repr__(self):
        return f"<{self.__class__.__name__}('{self.name}')>"

    @classmethod
    def user_info(cls):
        return cls('USER_INFO')

    @classmethod
    def app_status(cls):
        return cls('APP_STATUS')

    @classmethod
    def logs(cls):
        return cls('LOGS')

    @classmethod
    def full_logs(cls):
        return cls('FULL_LOGS')

    @classmethod
    def start(cls):
        return cls('START')

    @classmethod
    def stop(cls):
        return cls('STOP')

    @classmethod
    def restart(cls):
        return cls('RESTART')

    @classmethod
    def backup(cls):
        return cls('RESTART')

    @classmethod
    def commit(cls):
        return cls('COMMIT')

    @classmethod
    def delete(cls):
        return cls('DELETE')

    @classmethod
    def upload(cls):
        return cls('UPLOAD')


class Router:
    """Represents a route"""
    BASE: str = 'https://api.squarecloud.app/v1/public'

    # noinspection StrFormat
    def __init__(self, endpoint: Endpoint, **params) -> None:
        self.endpoint: Endpoint = endpoint
        self.method: str = endpoint.method
        self.path: str = endpoint.path
        url: str = self.BASE + self.path.format(**params)
        if params:
            url.format(params)
        self.url = url


class HTTPClient:
    """A client that handles requests and responses"""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.__session = aiohttp.ClientSession
        self._trace_configs: list[aiohttp.TraceConfig] = []

    async def request(self, route: Router, **kwargs) -> Response:
        """
        Sends a request to the Square API and returns the response.

        Args:
            route: the route to send a request
        Returns:
            RawResponseData
        """
        headers = {'Authorization': self.api_key}

        if route.method == 'POST':
            kwargs['skip_auto_headers'] = {'Content-Type'}

        if route.endpoint in (Endpoint.commit(), Endpoint.upload()):
            del kwargs['skip_auto_headers']
            file = kwargs['file']
            kwargs.pop('file')
            form = aiohttp.FormData()
            form.add_field('file', file.bytes, filename=file.name)
            kwargs['data'] = form

        async with self.__session(
                headers=headers, trace_configs=self._trace_configs) as session:
            async with session.request(url=route.url, method=route.method,
                                       **kwargs) as resp:
                status_code = resp.status
                data: RawResponseData = await resp.json()
                extra = {
                    'status': data.get('status'),
                    'route': route.url,
                    'code': data.get('code'),
                    'request_message': data.get('message', '')
                }
                match status_code:
                    case 200:
                        extra.pop('code')
                        logger.debug(msg='request to route: ', extra=extra)
                        response: Response = Response(data=data, route=route)
                    case 404:
                        logger.debug(msg='request to route: ', extra=extra)
                        msg = f'route [{route.endpoint.name}] returned 404, [{data.get("code")}]'
                        raise NotFoundError(msg)
                    case 401:
                        logger.error(msg='request to: ', extra=extra)
                        msg = 'Invalid api token has been passed'
                        raise AuthenticationFailure(msg)
                    case 400:
                        logger.error(msg='request to: ', extra=extra)
                        msg = f'route [{route.endpoint.name}] returned 400, [{data.get("code")}]'
                        raise BadRequestError(msg)
                    case _:
                        msg = f'An unexpected error occurred while requesting {route.url}, ' \
                              f'route: [{route.endpoint.name}], status: {data.get("statusCode")}\n' \
                              f'Error: {data.get("error")}'
                        raise RequestError(msg)
                return response

    async def fetch_user_info(self) -> Response:
        """
        Make a request to USER_INFO route

        Returns:
            Response
        """
        route = Router(Endpoint.user_info())
        response: Response = await self.request(route)
        return response

    async def fetch_app_status(self, app_id: str) -> Response:
        """
        Make a request for STATUS route

        Args:
            app_id:

        Returns:
            Response
        """
        route: Router = Router(Endpoint.app_status(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def fetch_logs(self, app_id: str) -> Response:
        """
        Make a request for LOGS route

        Args:
            app_id:

        Returns:
            Response
        """
        route: Router = Router(Endpoint.logs(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def fetch_logs_complete(self, app_id: str) -> Response:
        """
        Make a request for LOGS_COMPLETE route

        Args:
            app_id:

        Returns:
            Response
        """
        route: Router = Router(Endpoint.full_logs(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def start_application(self, app_id: str) -> Response:
        """
        Make a request for START route

        Args:
            app_id: the application ID

        Returns:
            Response
        """
        route: Router = Router(Endpoint.start(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def stop_application(self, app_id: str) -> Response:
        """
        Make a request for STOP route

        Args:
            app_id: the application ID

        Returns:
            Response
        """
        route: Router = Router(Endpoint.stop(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def restart_application(self, app_id: str) -> Response:
        """
        Make a request for RESTART route

        Args:
            app_id: the application ID

        Returns:
            Response
        """
        route: Router = Router(Endpoint.restart(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def backup(self, app_id: str) -> Response:
        """
        Make a request for BACKUP route
        Args:
            app_id: the application ID

        Returns:
            Response
        """
        route: Router = Router(Endpoint.backup(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def delete_application(self, app_id: str) -> Response:
        """
        Make a request for DELETE route
        Args:
            app_id: the application ID
        """
        route: Router = Router(Endpoint.delete(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def commit(self, app_id: str, file: File) -> Response:
        """
        Make a request for COMMIT route
        Args:
            app_id: the application ID
            file: the file to be committed

        Returns:
            Response
        """
        route: Router = Router(Endpoint.commit(), app_id=app_id)
        response: Response = await self.request(route, file=file)
        return response

    async def upload(self, file: File):
        """
        Make a request to UPLOAD route
        Args:
            file: file to be uploaded

        Returns:
            Response
        """
        route: Router = Router(Endpoint.upload())
        response: Response = await self.request(route, file=file)
        return response
