import asyncio
from typing import Any, Callable

from ..http import Endpoint, Response


class RequestListenerManager:
    """CaptureListenerManager"""

    def __init__(self):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance variables that will be used by other methods
        in the class.


        :param self: Refer to the class instance
        :return: A dictionary of the capture listeners and request listeners
        """
        self.request_listeners: dict[str, Callable] = {}

    def get_request_listener(self, endpoint: Endpoint) -> Callable:
        """
        The get_request_listener function is a helper function that returns
        the request listener for an endpoint.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Get the name of the endpoint
        :return: The request listener for a given endpoint
        """
        return self.request_listeners.get(endpoint.name)

    def add_request_listener(self, endpoint: Endpoint, call: Callable) -> None:
        """
        The add_request_listener function adds a request listener to the list
        of listeners.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Specify the endpoint that you want to
        listen for
        :param call: Callable: Specify the function that will be called when a
        request is received
        :return: None
        """
        if not self.get_request_listener(endpoint):
            return self.request_listeners.update({endpoint.name: call})

    def remove_request_listener(self, endpoint: Endpoint) -> Callable:
        """
        The remove_request_listener function removes a request listener from
        the capture_listeners dictionary.
        The function takes an endpoint as its only argument and returns
        the removed request listener.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Identify the endpoint that is being removed
        from the capture_listeners dictionary
        :return: The listener that was removed
        """
        if self.get_request_listener(endpoint):
            return self.request_listeners.pop(endpoint.name)

    def clear_request_listeners(self) -> None:
        """
        The clear_request_listeners function clears the capture_listeners list.

        :param self: Refer to the class instance
        :return: None
        """
        self.request_listeners = None

    async def notify(self, endpoint: Endpoint, response: Response) -> Any:
        """
        The on_request function is called when a request has been made to the
        endpoint.
        The response object contains all the information about the request

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Get the endpoint that was called
        :param response: Response: Get the response from the endpoint
        :return: The result of the call function
        """
        call: Callable = self.get_request_listener(endpoint)
        if not call:
            return
        if asyncio.iscoroutinefunction(call):
            return await call(response=response)
        return call(response=response)
