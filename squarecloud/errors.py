from typing import Callable


class SquareException(Exception):
    """abstract class SquareException"""

    def __init__(self, message: str = 'An unexpected error occurred'):
        self.message = message

    def __str__(self):
        return self.message


class RequestError(SquareException):
    """raised when a request fails"""

    def __init__(
        self, route: str, status_code: int, code: str, *args, **kwargs
    ):
        self.route = route
        self.status = status_code
        self.code = code
        self.message = f'route [{route}] returned {status_code}, [{code}]'
        super().__init__(self.message)


class AuthenticationFailure(RequestError):
    """raised when an API token is invalid"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = (
            'Authentication failed: ' 'Invalid API token or access denied'
        )


class NotFoundError(RequestError):
    """raises when a request returns a 404 response"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Resource not found: 404'


class BadRequestError(RequestError):
    """raises when a request returns a 400 response"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ApplicationNotFound(SquareException):
    """raises when an application is not found"""

    def __init__(self, app_id: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_id = app_id
        self.message = f'No application was found with id: {app_id}'


class InvalidFile(SquareException):
    """raised when a file is invalid"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Invalid file'


class MissingConfigFile(RequestError):
    """raised when the configuration file is missing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Configuration file is missing'


class MissingDependenciesFile(RequestError):
    """raised when the dependencies file is missing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Dependencies file is missing'


class TooManyRequests(RequestError):
    """raised when there are too many requests"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Too many requests'


class FewMemory(RequestError):
    """
    raised when there is insufficient memory available to host an application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Insufficient memory available'


class BadMemory(RequestError):
    """
    raised when the user has no memory to host an application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'No memory available'


class InvalidConfig(RequestError):
    """
    raised when the config file is corrupt or invalid.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'invalid config file'


class InvalidDisplayName(InvalidConfig):
    """
    raised when the display name in the config file is invalid.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Invalid display name in config file'


class MissingDisplayName(InvalidConfig):
    """
    raised when the display name in the config file is missing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Display name is missing in the config file'


class InvalidMain(InvalidConfig):
    """
    raised when the main file in the config file is invalid.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Invalid main file in config file'


class MissingMainFile(InvalidConfig):
    """
    raised when the main file in the config file is missing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Main file is missing in the config file'


class InvalidMemory(InvalidConfig):
    """
    raised when the memory value in the config file is invalid.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Invalid memory value in config file'


class MissingMemory(InvalidConfig):
    """
    raised when the memory value in the config file is missing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Memory value is missing in the config file'


class InvalidVersion(InvalidConfig):
    """
    raised when the version value in the config file is invalid.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Invalid version value in config file'


class MissingVersion(InvalidConfig):
    """
    raised when the version value in the config file is missing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Version value is missing in the config file'


class InvalidAccessToken(RequestError):
    """
    raised when the GitHub access token provided by the user is invalid.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InvalidDomain(RequestError):
    """
    raised when an invalid domain is provided
    """

    def __init__(self, domain: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = f'"{domain}" is a invalid custom domain'


class InvalidStart(InvalidConfig):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Invalid start value in configuration file'


class InvalidListener(SquareException):
    def __init__(self, listener: Callable, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.listener = listener
