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
from .. import File


class Response:
    """Represents a request response"""

    def __init__(self, data: RawResponseData, route: Router) -> None:
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and defines all of its
        attributes.


        :param self: Represent the instance of the class
        :param data: RawResponseData: Pass the data from the response to this
        class
        :param route: Router: Store the route of the request
        :return: None
        """
        self.data = data
        self.route: Router = route
        self.status: Literal['success', 'error'] = data.get('status')
        self.code: int = data.get('code')
        self.message: str = data.get('message')
        self.response: dict[str, Any] | list[Any] = data.get('response')

    def __repr__(self):
        """
        The __repr__ function is used to compute the &quot;official&quot;
        string representation of an object.
        This is how you would make an object of the class.

        :param self: Refer to the instance of the class
        :return: The name of the class and the status
        """
        return f'{Response.__name__}({self.status})'


class HTTPClient:
    """A client that handles requests and responses"""

    def __init__(self, api_key: str) -> None:
        """
        The __init__ function is called when the class is instantiated.
        It sets up the class with all of its attributes and other things it
        needs to function properly.

        :param self: Represent the instance of the class
        :param api_key: str: Store the api key that is passed in when the
        class is instantiated
        :return: None
        """
        self.api_key = api_key
        self.__session = aiohttp.ClientSession

    async def request(self, route: Router,
                      **kwargs) -> Response | None | bytes:
        """
        Sends a request to the Square API and returns the response.

        Args:
            route: the route to send a request
        Returns:
            RawResponseData
        """
        headers = {'Authorization': self.api_key}

        if route.endpoint in (Endpoint.commit(), Endpoint.upload()):
            file = kwargs.pop('file')
            form = aiohttp.FormData()
            form.add_field('file', file.bytes, filename=file.filename)
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
                        logger.debug(msg='request to route: ', extra=extra)
                        extra.pop('code')
                        response: Response = Response(data=data, route=route)
                    case 404:
                        logger.debug(msg='request to route: ', extra=extra)
                        msg = f'route [{route.endpoint.name}] returned 404, [{data.get("code")}]'
                        if route.endpoint == Endpoint.logs():
                            return
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
        route: Router = Router(Endpoint.delete_app(), app_id=app_id)
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

    async def upload(self, file: File) -> Response:
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

    async def fetch_app_files_list(self, app_id: str, path: str) -> Response:
        """
        The fetch_app_files_list function returns a list of files in the
        specified path.

        :param self: Represent the instance of the class
        :param app_id: str: Specify the application id to be used in the
        request
        :param path: str: Specify the path of the file
        :return: A Response object
        """
        route: Router = Router(Endpoint.files_list(), app_id=app_id, path=path)
        response: Response = await self.request(route)
        return response

    async def read_app_file(self, app_id: str, path: str) -> Response:
        """
        The read_app_file function reads the contents of a file in an app.

        :param self: Represent the instance of the class
        :param app_id: str: Specify the app id of the application you want to
        read from
        :param path: str: Specify the path of the file to be read
        :return: A Response object
        """
        route: Router = Router(Endpoint.files_read(), app_id=app_id, path=path)
        response: Response = await self.request(route)
        return response

    async def create_app_file(self, app_id: str, file: list[bytes],
                              path: str) -> Response:
        """
        The create_app_file function creates a file in the specified app.

        :param self: Reference the object that is calling the function
        :param app_id: str: Specify the app that you want to create a file for
        :param file: list[bytes]: Specify the file to be uploaded
        :param path: str: Specify the path of the file
        :return: A Response object
        """
        route: Router = Router(Endpoint.files_create(), app_id=app_id)
        response: Response = await self.request(route, json={'buffer': file,
                                                             'path': path})
        return response

    async def file_delete(self, app_id: str, path: str) -> Response:
        """
        The file_delete function deletes a file from the application.

        :param self: Represent the instance of a class
        :param app_id: str: Identify the application
        :param path: str: Specify the path of the file to be deleted
        :return: A Response object
        """
        route: Router = Router(Endpoint.files_delete(), app_id=app_id,
                               path=path)
        response: Response = await self.request(route)
        return response

    async def get_statistics(self) -> Response:
        """
        The get_statistics function returns the statistics of the current
        market.

        :param self: Access the attributes and methods of a class
        :return: A Response object
        """
        route: Router = Router(Endpoint.statistics())
        response: Response = await self.request(route)
        return response

    async def get_app_data(self, app_id: str) -> Response:
        """
        The get_app_data function returns a Response object containing the
        app data for the specified app_id.

        :param self: Refer to the current instance of a class
        :param app_id: str: Specify the app_id of the application you want to
        get data
        :return: A Response object
        """
        route: Router = Router(Endpoint('APP_DATA'), app_id=app_id)
        response: Response = await self.request(route)
        return response
