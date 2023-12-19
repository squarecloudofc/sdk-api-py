class SquareException(BaseException):
    """abstract class SquareException"""

    def __init__(self, message: str = 'An unexpected error occurred'):
        self.message = message

    def __str__(self):
        return self.message


class RequestError(SquareException):
    """raised when a request fails"""

    def __init__(self, route: str, status_code: int, code: str):
        self.route = route
        self.status = status_code
        self.code = code
        self.message = f'route [{route}] returned {status_code}, [{code}]'
        super().__init__(self.message)


class AuthenticationFailure(RequestError):
    """raised when an API token is invalid"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Authentication failed: Invalid API token'


class NotFoundError(RequestError):
    """raises when a request returns a 404 response"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Resource not found: 404'


class BadRequestError(RequestError):
    """raises when a request returns a 400 response"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = 'Bad request: 400'


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
