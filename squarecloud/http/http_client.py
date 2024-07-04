from __future__ import annotations

import logging
from typing import Any, Literal, Type

import aiohttp

from squarecloud.file import File

from ..errors import (
    AuthenticationFailure,
    BadMemory,
    BadRequestError,
    FewMemory,
    InvalidAccessToken,
    InvalidDisplayName,
    InvalidDomain,
    InvalidMain,
    InvalidMemory,
    InvalidStart,
    InvalidVersion,
    MissingConfigFile,
    MissingDependenciesFile,
    MissingDisplayName,
    MissingMainFile,
    MissingMemory,
    MissingVersion,
    NotFoundError,
    RequestError,
    TooManyRequests,
)
from ..logging import logger
from .endpoints import Endpoint, Router


class Response:
    """Represents a request response"""

    def __init__(self, data: dict[str, Any], route: Router) -> None:
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
        The __repr__ function is used to compute the string representation of
        an object.

        :param self: Refer to the instance of the class
        :return: The name of the class and the data of the response
        """
        return f'{Response.__name__}({self.data})'


def _get_error(code: str) -> type[RequestError] | None:
    """
    The _get_error function is a helper function that takes in an error code
    and returns the corresponding error class.
    This allows us to easily map errors to their respective classes,
    which makes it easier for us to raise them when we need to.

    :param code: str: Determine which error to raise
    :return: An error class
    :doc-author: Trelent
    """
    errors = {
        'FEW_MEMORY': FewMemory,
        'BAD_MEMORY': BadMemory,
        'MISSING_CONFIG': MissingConfigFile,
        'MISSING_DEPENDENCIES_FILE': MissingDependenciesFile,
        'MISSING_MAIN': MissingMainFile,
        'INVALID_MAIN': InvalidMain,
        'INVALID_DISPLAY_NAME': InvalidDisplayName,
        'MISSING_DISPLAY_NAME': MissingDisplayName,
        'INVALID_MEMORY': InvalidMemory,
        'MISSING_MEMORY': MissingMemory,
        'INVALID_VERSION': InvalidVersion,
        'MISSING_VERSION': MissingVersion,
        'INVALID_ACCESS_TOKEN': InvalidAccessToken,
        'REGEX_VALIDATION': InvalidDomain,
        'INVALID_START': InvalidStart,
    }
    error_class = errors.get(code, None)
    if error_class is None:
        return
    else:
        return error_class


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
        self._last_response: Response | None = None

    async def request(self, route: Router, **kwargs) -> Response | bytes:
        """
        Sends a request to the Square API and returns the response.

        :param route: the route to send a request
        :param kwargs: Keyword arguments
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        :raises FewMemory: Raised when user memory reached the maximum
                amount of memory
        :raises BadMemory: Raised when the memory in configuration file is
                invalid
        :raises MissingConfigFile: Raised when the .zip file is missing the
                config file (squarecloud.app/squarecloud.config)
        :raises MissingDependenciesFile: Raised when the .zip file is missing
                the dependencies file (requirements.txt, package.json, ...)
        :raises MissingMainFile: Raised when the .zip file is missing the main
                file (main.py, index.js, ...)
        :raises InvalidMain: Raised when the field MAIN in config file is
                invalid or when the main file is corrupted
        :raises InvalidDisplayName: Raised when the field DISPLAY_NAME
                in config file is invalid
        :raises MissingDisplayName: Raised when the DISPLAY_NAME field is
                missing in the config file
        :raises InvalidMemory: Raised when the MEMORY field is invalid
        :raises MissingMemory: Raised when the MEMORY field is missing in
                the config file
        :raises InvalidVersion: Raised when the VERSION field is invalid,
                the value accepted is "recommended" or "latest"
        :raises MissingVersion: Raised when the VERSION field is missing in
                the config file
        :raises InvalidAccessToken: Raised when a GitHub access token
                provided is invalid
        :raises InvalidDomain: Raised when a domain provided is invalid
        """
        headers = {
            'Authorization': self.api_key,
            'User-Agent': 'squarecloud-api/3.5.1',
        }
        extra_error_kwargs: dict[str, Any] = {}

        if kwargs.get('custom_domain'):
            extra_error_kwargs['domain'] = kwargs.pop('custom_domain')

        if route.endpoint in (Endpoint.commit(), Endpoint.upload()):
            file = kwargs.pop('file')
            form = aiohttp.FormData()
            form.add_field('file', file.bytes, filename=file.filename)
            kwargs['data'] = form
        async with self.__session(headers=headers) as session:
            async with session.request(
                url=route.url, method=route.method, **kwargs
            ) as resp:
                status_code = resp.status
                data: dict[str, Any] = await resp.json()
                response = Response(data=data, route=route)
                self._last_response = response

                code: str | None = data.get('code')
                error: Type[RequestError] | None = None
                log_msg = '{status} request to route: {route}'
                log_msg = log_msg.format(
                    status=data.get('status'),
                    route=route.url,
                )

                if code:
                    log_msg += f' with code: {code}'
                log_level: int

                match status_code:
                    case 200:
                        log_level = logging.DEBUG
                    case 404:
                        if code is None:
                            log_level = logging.DEBUG
                        else:
                            log_level = logging.ERROR
                            error = NotFoundError
                    case 400:
                        log_level = logging.ERROR
                        error = BadRequestError
                    case 401:
                        log_level = logging.ERROR
                        error = AuthenticationFailure
                    case 429:
                        log_level = logging.ERROR
                        error = TooManyRequests
                    case _:
                        error = RequestError

                if _ := _get_error(code):
                    log_level = logging.ERROR
                    error = _
                logger.log(log_level, log_msg, extra={'type': 'http'})
                if error:
                    raise error(
                        **extra_error_kwargs,
                        route=route.endpoint.name,
                        status_code=status_code,
                        code=code,
                    )
                return response

    async def fetch_user_info(self) -> Response:
        """
        Fetches user information and returns the response object

        :return: A Response object
        :rtype: Response

        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route = Router(Endpoint.user())
        response: Response = await self.request(route)
        return response

    async def fetch_app_status(self, app_id: str) -> Response:
        """
        Fetches status of a hosted application

        :param app_id:  The application id
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.app_status(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def fetch_logs(self, app_id: str) -> Response | None:
        """
        Fetches logs of a hosted application

        :param app_id: The application id
        :return: A Response object or None

        :rtype: Response | None

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.logs(), app_id=app_id)
        return await self.request(route)

    async def start_application(self, app_id: str) -> Response:
        """
        Start a hosted application

        :param app_id: The application id
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.start(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def stop_application(self, app_id: str) -> Response:
        """
        Stop a hosted application

        :param app_id: The application id
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.stop(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def restart_application(self, app_id: str) -> Response:
        """
        Restart a hosted application

        :param app_id: The application id
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.restart(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def backup(self, app_id: str) -> Response:
        """
        Backup a hosted application

        :param app_id: The application id
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.backup(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def delete_application(self, app_id: str) -> Response:
        """
        Delete a hosted application

        :param app_id: The application id
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.delete_app(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def commit(self, app_id: str, file: File) -> Response:
        """
        Commit a file to an application

        :param app_id: The application id
        :param file: A File object to be committed
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.commit(), app_id=app_id)
        response: Response = await self.request(route, file=file)
        return response

    async def upload(self, file: File) -> Response:
        """
        Upload a new application

        :param file: A File object to be uploaded
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        :raises FewMemory: Raised when user memory reached the maximum
                amount of memory
        :raises BadMemory: Raised when the memory in configuration file is
                invalid
        :raises MissingConfigFile: Raised when the .zip file is missing the
                config file (squarecloud.app/squarecloud.config)
        :raises MissingDependenciesFile: Raised when the .zip file is missing
                the dependencies file (requirements.txt, package.json, ...)
        :raises MissingMainFile: Raised when the .zip file is missing the main
                file (main.py, index.js, ...)
        :raises InvalidMain: Raised when the field MAIN in config file is
                invalid or when the main file is corrupted
        :raises InvalidDisplayName: Raised when the field DISPLAY_NAME
                in config file is invalid
        :raises MissingDisplayName: Raised when the DISPLAY_NAME field is
                missing in the config file
        :raises InvalidMemory: Raised when the MEMORY field is invalid
        :raises MissingMemory: Raised when the MEMORY field is missing in
                the config file
        :raises InvalidVersion: Raised when the VERSION field is invalid,
                the value accepted is "recommended" or "latest"
        :raises MissingVersion: Raised when the VERSION field is missing in
                the config file
        :raises InvalidAccessToken: Raised when a GitHub access token
                provided is invalid
        :raises InvalidDomain: Raised when a domain provided is invalid
        """
        route: Router = Router(Endpoint.upload())
        response: Response = await self.request(route, file=file)
        return response

    async def fetch_app_files_list(self, app_id: str, path: str) -> Response:
        """
        Fetches the files list of the application

        :param app_id: The application id
        request
        :param path: Specify the directory path
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.files_list(), app_id=app_id, path=path)
        response: Response = await self.request(route)
        return response

    async def read_app_file(self, app_id: str, path: str) -> Response:
        """
        The read_app_file function reads the contents of a file in an app.

        :param app_id: The application id
        :param path: Specify the path of the file to be read
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.files_read(), app_id=app_id, path=path)
        response: Response = await self.request(route)
        return response

    async def create_app_file(
        self, app_id: str, file: list[bytes], path: str
    ) -> Response:
        """
        The create_app_file method creates a file in the specified app.

        :param app_id: The application id
        :param file: Specify the file to be uploaded
        :param path: str: Specify the path of the file
        :return: A Response object

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.files_create(), app_id=app_id)
        response: Response = await self.request(
            route, json={'buffer': file, 'path': '/' + path}
        )
        return response

    async def file_delete(self, app_id: str, path: str) -> Response:
        """
        The file_delete method deletes a file from the application.

        :param app_id: The application id
        :param path: Specify the path of the file to be deleted
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(
            Endpoint.files_delete(), app_id=app_id, path=path
        )
        response: Response = await self.request(route)
        return response

    async def get_app_data(self, app_id: str) -> Response:
        """
        The get_app_data method returns a Response object containing the
        app data for the specified app_id.

        :param app_id: The application id
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.app_data(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def get_last_deploys(self, app_id: str) -> Response:
        """
        The get_last_deploys method returns the last deploys of an
        application.

        :param app_id: The application id
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.last_deploys(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    async def create_github_integration(
        self, app_id: str, github_access_token: str
    ) -> Response:
        """
        The create_github_integration method returns a webhook to integrate
        with a GitHub repository.

        :param app_id: The application id
        :param github_access_token: GitHub access token
        :return: A Response object
        :rtype: Response

        :raises InvalidAccessToken: Raised when a GitHub access token
                provided is invalid
        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.github_integration(), app_id=app_id)
        body = {'access_token': github_access_token}
        response: Response = await self.request(route, json=body)
        return response

    async def update_custom_domain(
        self, app_id: str, custom_domain: str
    ) -> Response:
        """
        The update_custom_domain method updates the custom domain of an app.

        :param app_id: The application id
        :param custom_domain: Set the custom domain for the app
        :return: A Response object
        :rtype: Response

        :raises InvalidDomain: Raised when a domain provided is invalid
        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(
            Endpoint.custom_domain(),
            app_id=app_id,
            custom_domain=custom_domain,
        )
        response: Response = await self.request(
            route, custom_domain=custom_domain
        )
        return response

    async def domain_analytics(self, app_id: str) -> Response:
        """
        The domain_analytics method returns a list of all domains analytics
        for the specified app.

        :param app_id: The application id
        :return: A Response object

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        route: Router = Router(Endpoint.domain_analytics(), app_id=app_id)
        response: Response = await self.request(route)
        return response

    @property
    def last_response(self) -> Response | None:
        """
        Returns the last response made

        :return: A Response object or None
        :rtype: Response | None
        """
        return self._last_response
