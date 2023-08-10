class SquareException(BaseException):
    """abstract class SquareException"""


class RequestError(SquareException):
    """raised when a request fails"""

    def __init__(self, route: str, status_code: int, code: str):
        self.route = route
        self.status = status_code
        self.code = code
        message = f'route [{route}] returned {status_code}, [{code}]'
        super().__init__(message)


class AuthenticationFailure(RequestError):
    """raised when an API token is invalid"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NotFoundError(RequestError):
    """raises when a request returns a 404 response"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BadRequestError(RequestError):
    """raises when a request returns a 400 response"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ApplicationNotFound(SquareException):
    """raises when an application is not found"""


class InvalidFile(SquareException):
    """raised when a file is invalid"""


class MissingConfigFile(RequestError):
    """raised when the configuration file is missing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MissingDependenciesFile(RequestError):
    """raised when the configuration file is missing"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TooManyRequests(RequestError):
    """raised when there are too many requests"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FewMemory(RequestError):
    """
    raised when there is insufficient memory available to host an application.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
