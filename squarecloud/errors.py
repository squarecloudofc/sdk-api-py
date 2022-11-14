class SquareException(BaseException):
    """abstract class SquareException"""


class RequestError(SquareException):
    """raised when a request fails"""


class AuthenticationFailure(RequestError):
    """raised when an API token is invalid"""


class NotFoundError(RequestError):
    """raises when a request returns a 404 response"""


class BadRequestError(RequestError):
    """raises when a request returns a 400 response"""
