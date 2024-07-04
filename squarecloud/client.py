"""This module is a wrapper for using the SquareCloud API"""
from __future__ import annotations

from functools import wraps
from io import BytesIO
from typing import Any, Callable, Literal, ParamSpec, TextIO, TypeVar

from typing_extensions import deprecated

from .app import Application
from .data import (
    AppData,
    BackupData,
    DeployData,
    DomainAnalytics,
    FileInfo,
    LogsData,
    StatusData,
    UploadData,
    UserData,
)
from .errors import ApplicationNotFound, InvalidFile, SquareException
from .file import File
from .http import HTTPClient, Response
from .http.endpoints import Endpoint
from .listeners import Listener, ListenerConfig
from .listeners.request_listener import RequestListenerManager
from .logging import logger

P = ParamSpec('P')
R = TypeVar('R')


@deprecated(
    'create_config_file is deprecated, '
    'use squarecloud.utils.ConfigFile instead.'
)
def create_config_file(
    path: str,
    display_name: str,
    main: str,
    memory: int,
    version: Literal['recommended', 'latest'] = 'recommended',
    description: str | None = None,
    subdomain: str | None = None,
    start: str | None = None,
    auto_restart: bool = False,
    **kwargs,
) -> TextIO | str:
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
    :param description: str | None: Specify a description for the app
    :param subdomain: str | None: Specify the subdomain of your app
    :param start: str | None: Specify the command that should be run when the
    application starts
    :param auto_restart: bool | None: Determine if the app should restart
    automatically after a crash
    :return: File content
    :rtype: str
    """
    content: str = ''
    optionals: dict[str, Any] = {
        'DISPLAY_NAME': display_name,
        'MAIN': main,
        'MEMORY': memory,
        'VERSION': version,
        'DESCRIPTION': description,
        'SUBDOMAIN': subdomain,
        'START': start,
        'AUTORESTART': auto_restart,
    }
    for key, value in optionals.items():
        if value:
            string: str = f'{key}={value}\n'
            content += string
    if kwargs.get('save', True):
        with open(f'./{path}/squarecloud.app', 'w', encoding='utf-8') as file:
            file.write(content)
        return file
    return content


class Client(RequestListenerManager):
    """A client for interacting with the SquareCloud API."""

    def __init__(
        self,
        api_key: str,
        log_level: Literal[
            'DEBUG',
            'INFO',
            'WARNING',
            'ERROR',
            'CRITICAL',
        ] = 'INFO',
    ) -> None:
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and defines all of its
        attributes.


        :param self: Refer to the class instance
        :param api_key: str: Your API key, get in:
         https://squarecloud.app/dashboard/me
        :param debug: bool: Set the logging level to debug
        :return: None
        """
        self.log_level = log_level
        self._api_key = api_key
        self._http = HTTPClient(api_key=api_key)
        self.logger = logger
        logger.setLevel(log_level)
        super().__init__()

    @property
    def api_key(self) -> str:
        """
        Returns the api key for the client.

        :return: The api key
        :rtype: str
        """
        return self._api_key

    def on_request(self, endpoint: Endpoint, **kwargs):
        """
        The on_request function is a decorator that allows you to register a
        function as an endpoint listener.

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
            :raises SquarecloudException: Raised if the endpoint is already
                    registered
            """
            for key, value in kwargs.items():
                if key not in ListenerConfig.__annotations__:
                    raise ValueError(
                        f'Invalid listener configuration: "{key}={value}"'
                    )
            config = ListenerConfig(**kwargs)
            listener = Listener(
                endpoint=endpoint, callback=func, client=self, config=config
            )
            self.include_listener(listener)

        return wrapper

    @staticmethod
    def _notify_listener(endpoint: Endpoint):
        """
        The _notify_listener function is a decorator that call a listener after
        the decorated coroutine is called

        :param endpoint: the endpoint for witch the listener will fetch
        :return: a callable
        """

        def wrapper(func: Callable[P, R]) -> Callable[P, R]:
            @wraps(func)
            async def decorator(
                self: Client, *args: P.args, **kwargs: P.kwargs
            ) -> R:
                # result: Any
                response: Response
                result = await func(self, *args, **kwargs)
                response = self._http.last_response
                if kwargs.get('avoid_listener', False):
                    return result
                await self.notify(
                    endpoint=endpoint,
                    response=response,
                    extra=kwargs.get('extra'),
                )
                return result

            return decorator

        return wrapper

    @_notify_listener(Endpoint.user())
    async def user(self, **_kwargs) -> UserData:
        """
        This method is used to get your information.

        :param _kwargs: Keyword arguments
        :return: A UserData object
        :rtype: UserData

        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.fetch_user_info()
        payload: dict[str, Any] = response.response
        return UserData(**payload['user'])

    @_notify_listener(Endpoint.logs())
    async def get_logs(self, app_id: str, **_kwargs) -> LogsData:
        """
        The get_logs method is used to get logs for an application.

        :param app_id: Specify the application by id
        :param _kwargs: Keyword arguments
        :return: A LogsData object
        :rtype: LogsData

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.fetch_logs(app_id)
        payload: dict[str, Any] | None = response.response
        if not payload:
            logs_data: LogsData = LogsData()
        else:
            logs_data: LogsData = LogsData(**payload)

        return logs_data

    @_notify_listener(Endpoint.app_status())
    async def app_status(self, app_id: str, **_kwargs) -> StatusData:
        """
        The app_status method is used to get the status of an application.

        :param app_id: Specify the application by id
        :param _kwargs: Keyword arguments
        :return: A StatusData object
        :rtype: StatusData

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.fetch_app_status(app_id)
        payload: dict[str, Any] = response.response
        return StatusData(**payload)

    @_notify_listener(Endpoint.start())
    async def start_app(self, app_id: str, **_kwargs) -> Response:
        """
        The start_app method starts an application.

        :param app_id: Specify the application by id
        :param _kwargs: Keyword arguments
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        return await self._http.start_application(app_id)

    @_notify_listener(Endpoint.stop())
    async def stop_app(self, app_id: str, **_kwargs) -> Response:
        """
        The stop_app method stops an application.

        :param app_id: Specify the application by id
        :param _kwargs: Keyword arguments
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        return await self._http.stop_application(app_id)

    @_notify_listener(Endpoint.restart())
    async def restart_app(self, app_id: str, **_kwargs) -> Response:
        """
        The restart_app method is restarts an application.

        :param app_id: Specify the application id
        :param _kwargs: Keyword arguments
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        return await self._http.restart_application(app_id)

    @_notify_listener(Endpoint.backup())
    async def backup(self, app_id: str, **_kwargs) -> BackupData:
        """
        The backup method is used to backup an application.

        :param app_id: Specify the application id
        :param _kwargs: Keyword arguments
        :return: A BackupData object
        :rtype: BackupData

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.backup(app_id)
        payload: dict[str, Any] = response.response
        return BackupData(**payload)

    @_notify_listener(Endpoint.delete_app())
    async def delete_app(self, app_id: str, **_kwargs) -> Response:
        """
        The delete_app method deletes an application.

        :param app_id: The application id
        :param _kwargs: Keyword arguments
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        return await self._http.delete_application(app_id)

    @_notify_listener(Endpoint.commit())
    async def commit(self, app_id: str, file: File, **_kwargs) -> Response:
        """
        The commit method is used to commit an application.

        :param app_id: Specify the application by id
        :param file: File: Specify the File object to be committed
        :param _kwargs: Keyword arguments
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        return await self._http.commit(app_id, file)

    @_notify_listener(Endpoint.user())
    async def app(self, app_id: str, **_kwargs) -> Application:
        """
        The app method returns an Application object.

        :param app_id: Specify the application by id
        :param _kwargs: Keyword arguments
        :return: An Application object
        :rtype: Application

        :raises ApplicationNotFound: Raised when is not found an application
                with the specified id
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.fetch_user_info()
        payload = response.response
        app_data = list(
            filter(
                lambda application: application['id'] == app_id,
                payload['applications'],
            )
        )
        if not app_data:
            raise ApplicationNotFound(app_id=app_id)
        app_data = app_data.pop()
        app_data['language'] = app_data.pop('lang')
        app_data = AppData(**app_data).to_dict()
        app_data['lang'] = app_data.pop('language')
        return Application(client=self, http=self._http, **app_data)

    @_notify_listener(Endpoint.user())
    async def all_apps(self, **_kwargs) -> list[Application]:
        """
        The all_apps method returns a list of all applications that the user
        has access to.

        :param _kwargs: Keyword arguments
        :return: A list of Application objects
        :rtype: list[Application]

        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.fetch_user_info()
        payload = response.response
        apps_data: list = payload['applications']
        apps: list[Application] = []
        for data in apps_data:
            data['language'] = data.pop('lang')
            data = AppData(**data).to_dict()
            data['lang'] = data.pop('language')
            apps.append(Application(client=self, http=self._http, **data))
        return apps

    @_notify_listener(Endpoint.upload())
    async def upload_app(self, file: File, **_kwargs) -> UploadData:
        """
        The upload_app method uploads an application to the server.

        :param file: Upload a file
        :param _kwargs: Keyword arguments
        :return: An UploadData object
        :rtype: UploadData

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
        if not isinstance(file, File):
            raise InvalidFile(f'you need provide an {File.__name__} object')

        if (file.filename is not None) and (
            file.filename.split('.')[-1] != 'zip'
        ):
            raise InvalidFile('the file must be a .zip file')
        response: Response = await self._http.upload(file)
        payload: dict[str, Any] = response.response
        return UploadData(**payload)

    @_notify_listener(Endpoint.files_list())
    async def app_files_list(
        self, app_id: str, path: str, **_kwargs
    ) -> list[FileInfo]:
        """
        The app_files_list method returns a list of your application files.

        :param app_id: Specify the application by id
        :param path: Specify the path to the file
        :param _kwargs: Keyword arguments
        :return: A list of FileInfo objects
        :rtype: list[FileInfo]

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.fetch_app_files_list(
            app_id, path
        )
        if not response.response:
            return []
        return [
            FileInfo(**data, app_id=app_id, path=path + f'/{data.get("name")}')
            for data in response.response
        ]

    @_notify_listener(Endpoint.files_read())
    async def read_app_file(
        self, app_id: str, path: str, **_kwargs
    ) -> BytesIO | None:
        """
        The read_app_file method reads a file from the specified path and
        returns a BytesIO representation.

        :param app_id: Specify the application by id
        :param path: str: Specify the path of the file to be read
        :param _kwargs: Keyword arguments
        :return: A BytesIO representation of the file
        :rtype: BytesIO | None

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.read_app_file(app_id, path)
        if response.response:
            return BytesIO(bytes(response.response.get('data')))

    @_notify_listener(Endpoint.files_create())
    async def create_app_file(
        self, app_id: str, file: File, path: str, **_kwargs
    ) -> Response:
        """
        The create_app_file method creates a new file in the specified
        directory.

        :param app_id: Specify the application by id
        :param file: Pass the file to be created
        :param path: Specify the directory to create the file in
        :param _kwargs: Keyword arguments
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        if not isinstance(file, File):
            raise SquareException(
                'the file must be an string or a squarecloud.File object'
            )
        file_bytes = list(file.bytes.read())
        response: Response = await self._http.create_app_file(
            app_id, file_bytes, path=path
        )
        file.bytes.close()

        return response

    @_notify_listener(Endpoint.files_delete())
    async def delete_app_file(
        self, app_id: str, path: str, **_kwargs
    ) -> Response:
        """
        The delete_app_file method deletes a file in the specified directory.

        :param app_id: Specify the application byd id
        :param path: Specify the directory where the file should be
        deleted
        :param _kwargs: Keyword arguments
        :return: A Response object
        :rtype: Response

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        return await self._http.file_delete(app_id, path)

    @_notify_listener(Endpoint.app_data())
    async def app_data(self, app_id: str, **_kwargs) -> AppData:
        """
        The app_data method is used to get application data.

        :param app_id: Specify the application by id
        :param _kwargs: Keyword arguments
        :return: An AppData object
        :rtype: AppData

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.get_app_data(app_id)
        return AppData(**response.response)

    @_notify_listener(Endpoint.last_deploys())
    async def last_deploys(
        self, app_id: str, **_kwargs
    ) -> list[list[DeployData]]:
        """
        The last_deploys method returns a list of DeployData objects.

        :param self: Represent the instance of a class
        :param app_id: str: Specify the application by id
        :param _kwargs: Keyword arguments
        :return: A list of DeployData objects
        :rtype: list[list[DeployData]]

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.get_last_deploys(app_id)
        data = response.response
        return [[DeployData(**deploy) for deploy in _] for _ in data]

    @_notify_listener(Endpoint.github_integration())
    async def github_integration(
        self, app_id: str, access_token: str, **_kwargs
    ) -> str:
        """
        The github_integration method returns a GitHub Webhook url to integrate
        with your GitHub repository

        :param app_id: Specify the application by id
        :param access_token: your GitHub access token
        :param _kwargs: Keyword arguments
        :return: A GitHub Webhook url

        :raises InvalidAccessToken: Raised when a GitHub access token
                provided is invalid
        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.create_github_integration(
            app_id=app_id, github_access_token=access_token
        )
        data = response.response
        return data.get('webhook')

    @_notify_listener(Endpoint.custom_domain())
    async def set_custom_domain(
        self, app_id: str, custom_domain: str, **_kwargs
    ) -> Response:
        """
        The set_custom_domain method sets a custom domain to your website

        :param app_id: Specify the application by id
        :param custom_domain: Specify the custom domain to use for your website
        :param _kwargs: Keyword arguments
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
        return await self._http.update_custom_domain(
            app_id=app_id, custom_domain=custom_domain
        )

    @_notify_listener(Endpoint.domain_analytics())
    async def domain_analytics(
        self, app_id: str, **_kwargs
    ) -> DomainAnalytics:
        """
        The domain_analytics method return a DomainAnalytics object

        :param app_id: Specify the application by id
        :param _kwargs: Keyword arguments
        :return: A DomainAnalytics object
        :rtype: DomainAnalytics

        :raises NotFoundError: Raised when the request status code is 404
        :raises BadRequestError: Raised when the request status code is 400
        :raises AuthenticationFailure: Raised when the request status
                code is 401
        :raises TooManyRequestsError: Raised when the request status
                code is 429
        """
        response: Response = await self._http.domain_analytics(
            app_id=app_id,
        )
        return DomainAnalytics(**response.response)
