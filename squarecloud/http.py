"""Module to manage requests"""
from __future__ import annotations

from typing import Dict, Any

import aiohttp

from .errors import RequestError, AuthenticationFailure, NotFoundError, BadRequestError
from .logs import logger
from .square import File
from .types import RawResponseData


class Response:
    """Represents a request response"""

    def __init__(self, data: RawResponseData) -> None:
        self.data = data
        self.status = data.get('status')
        self.code = data.get('code')
        self.message = data.get('message')
        self.response = data.get('response')


class Route:
    """Represents a route"""
    BASE: str = 'https://api.squarecloud.app/v1/public'
    ENDPOINTS = {
        'USER_INFO': {'METHOD': 'GET', 'PATH': '/user'},
        'APP_STATUS': {'METHOD': 'GET', 'PATH': '/status/{app_id}'},
        'LOGS': {'METHOD': 'GET', 'PATH': '/logs/{app_id}'},
        'LOGS_COMPLETE': {'METHOD': 'GET', 'PATH': '/full-logs/{app_id}'},
        'START': {'METHOD': 'POST', 'PATH': '/start/{app_id}'},
        'STOP': {'METHOD': 'POST', 'PATH': '/stop/{app_id}'},
        'RESTART': {'METHOD': 'POST', 'PATH': '/restart/{app_id}'},
        'BACKUP': {'METHOD': 'GET', 'PATH': '/backup/{app_id}'},
        'COMMIT': {'METHOD': 'POST', 'PATH': '/commit/{app_id}'},
        'DELETE': {'METHOD': 'POST', 'PATH': '/delete/{app_id}'},
    }

    # noinspection StrFormat
    def __init__(self, endpoint: str, **params) -> None:
        route: Dict[str: Dict[str, Any]] = self.ENDPOINTS[endpoint]
        self.endpoint = endpoint
        self.method: str = route['METHOD']
        self.path: str = route['PATH']
        url: str = self.BASE + self.path.format(**params)
        if params:
            url.format(params)
        self.url = url


class HTTPClient:
    """A client that handles requests and responses"""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.__session = aiohttp.ClientSession

    async def request(self, route: Route, **kwargs) -> Response:
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

        if 'file' in kwargs:
            del kwargs['skip_auto_headers']
            file = kwargs['file']
            kwargs.pop('file')
            form = aiohttp.FormData()
            form.add_field('file', file.file, filename=file.name)
            kwargs['data'] = form

        async with self.__session(headers=headers) as session:
            async with session.request(url=route.url, method=route.method, **kwargs) as resp:
                status_code = resp.status
                data: RawResponseData = await resp.json()
                extra = {
                    'status': data.get('status'),
                    'route': route.endpoint,
                    'code': data.get('code'),
                    'request_message': data.get('message', '')
                }
                if status_code == 200:
                    extra.pop('code')
                    logger.debug(msg='request to route: ', extra=extra)
                    response: Response = Response(data=data)
                elif status_code == 404:
                    logger.debug(msg='request to route: ', extra=extra)
                    msg = f'route [{route.endpoint}] returned 404, [{data.get("code")}]'
                    raise NotFoundError(msg)
                elif status_code == 401:
                    logger.error(msg='request to: ', extra=extra)
                    msg = f'Invalid api token has been passed: \033[4;31m{self.api_key}\033[m'
                    raise AuthenticationFailure(msg)
                elif status_code == 400:
                    logger.error(msg='request to: ', extra=extra)
                    msg = f'route [{route.endpoint}] returned 400, [{data.get("code")}]'
                    raise BadRequestError(msg)
                else:
                    msg = f'An unexpected error occurred while requesting {route.url}, ' \
                          f'route: [{route.endpoint}], status: {data.get("statusCode")}\n' \
                          f'Error: {data.get("error")}'
                    raise RequestError(msg)
                return response

    async def fetch_user_info(self) -> Response:
        """
        Make a request to USER_INFO route

        Returns:
            Response
        """
        route = Route('USER_INFO')
        response: Response = await self.request(route)
        return response

    async def fetch_app_status(self, app_id: int | str) -> Response:
        """
        Make a request for STATUS route

        Args:
            app_id:

        Returns:
            Response
        """
        route: Route = Route('APP_STATUS', app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def fetch_logs(self, app_id: int | str) -> Response:
        """
        Make a request for LOGS route

        Args:
            app_id:

        Returns:
            Response
        """
        route: Route = Route('LOGS', app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def fetch_logs_complete(self, app_id: int | str) -> Response:
        """
        Make a request for LOGS_COMPLETE route

        Args:
            app_id:

        Returns:
            Response
        """
        route: Route = Route('LOGS_COMPLETE', app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def start_application(self, app_id: int | str) -> Response:
        """
        Make a request for START route

        Args:
            app_id: the application ID

        Returns:
            Response
        """
        route: Route = Route('START', app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def stop_application(self, app_id: int | str) -> Response:
        """
        Make a request for STOP route

        Args:
            app_id: the application ID

        Returns:
            Response
        """
        route: Route = Route('STOP', app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def restart_application(self, app_id: int | str) -> Response:
        """
        Make a request for RESTART route

        Args:
            app_id: the application ID

        Returns:
            Response
        """
        route: Route = Route('RESTART', app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def backup(self, app_id: int | str) -> Response:
        """
        Make a request for BACKUP route
        Args:
            app_id: the application ID

        Returns:
            Response
        """
        route: Route = Route('BACKUP', app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def delete_application(self, app_id: int | str) -> Response:
        """
        Make a request for DELETE route
        Args:
            app_id: the application ID
        """
        route: Route = Route('DELETE', app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def commit(self, app_id: int | str, file: File) -> Response:
        """
        Make a request for COMMIT route
        Args:
            app_id: the application ID
            file: the file to be committed

        Returns:
            Response
        """
        route: Route = Route('COMMIT', app_id=app_id)
        response: Response = await self.request(route, file=file)
        return response
