from __future__ import annotations

from typing import Any, Literal

import aiohttp

from .endpoints import Endpoint, Router
from ..errors import (
    NotFoundError,
    RequestError,
    BadRequestError,
    AuthenticationFailure
)
from ..logs import logger
from ..payloads import RawResponseData
from ..square import File


class Response(aiohttp.ClientResponse):
    """Represents a request response"""

    def __init__(self, data: RawResponseData, route: Router, *args,
                 **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.data = data
        self.route: Router = route
        self.status: Literal['success', 'error'] = data.get('status')
        self.code: int = data.get('code')
        self.message: str = data.get('message')
        self.response: dict[str, Any] = data.get('response')
        self.app: dict[str, Any] = data.get('app')


class HTTPClient:
    """A client that handles requests and responses"""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.__session = aiohttp.ClientSession

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
            file = kwargs.pop('file')
            form = aiohttp.FormData()
            form.add_field('file', file.bytes, filename=file.name)
            kwargs['data'] = form
        async with self.__session(headers=headers) as session:
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

    async def fetch_user_info(self, user_id: int | None = None) -> Response:
        """
        Make a request to USER_INFO route

        Returns:
            Response
        """
        if user_id:
            route: Router = Router(Endpoint.user_info(), user_id=user_id)
            response: Response = await self.request(route)
            return response
        route = Router(Endpoint.user_me())
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
