import asyncio
from typing import Any, Callable

from .http import Response
from .http.endpoints import Endpoint


class ListenerManager:
    """ListenerManager"""

    def __init__(self):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance variables that will be used by other methods
        in the class.


        :param self: Refer to the instance of the class
        :return: A dictionary of the capture listeners and request listeners
        """
        self.capture_listeners: dict[str, Callable] = {}
        self.request_listeners: dict[str, Callable] = {}

    def get_capture_listener(self, endpoint: Endpoint) -> Callable:
        """
        The get_capture_listener function is used to get the capture listener
        for a given endpoint.

        :param self: Represent the instance of the class
        :param endpoint: Endpoint: Get the capture listener from the endpoint
        name
        :return: The capture listener for the given endpoint
        """
        return self.capture_listeners.get(endpoint.name)

    def add_capture_listener(self, endpoint: Endpoint, call: Callable) -> None:
        """
        The add_capture_listener function adds a listener to the
        capture_listeners dictionary.
        The key is the name of an endpoint, and the value is a callable
        function that will be called when
        the endpoint's data has been captured.

        :param self: Represent the instance of the class
        :param endpoint: Endpoint: Specify the endpoint that you want to
        listen to
        :param call: Callable: Define the function that will be called when a
        request is made to the endpoint
        :return: None
        """
        if not self.get_capture_listener(endpoint):
            return self.capture_listeners.update({endpoint.name: call})

    def remove_capture_listener(self, endpoint: Endpoint) -> Callable:
        """
        The remove_capture_listener function removes a capture listener from
        the list of listeners.

        :param self: Represent the instance of the class
        :param endpoint: Endpoint: Identify the endpoint to remove
        :return: The capture_listener that was removed from the dictionary
        """
        if self.get_capture_listener(endpoint):
            return self.capture_listeners.pop(endpoint.name)

    def clear_capture_listeners(self) -> None:
        """
        The clear_capture_listeners function clears the capture_listeners list.

        :param self: Represent the instance of the class
        :return: None
        """
        self.capture_listeners = None

    def get_request_listener(self, endpoint: Endpoint) -> Callable:
        """
        The get_request_listener function is a helper function that returns
        the request listener for an endpoint.

        :param self: Represent the instance of the class
        :param endpoint: Endpoint: Get the name of the endpoint
        :return: The request listener for a given endpoint
        """
        return self.request_listeners.get(endpoint.name)

    def add_request_listener(self, endpoint: Endpoint, call: Callable) -> None:
        """
        The add_request_listener function adds a request listener to the list
        of listeners.

        :param self: Represent the instance of the class
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

        :param self: Represent the instance of a class
        :param endpoint: Endpoint: Identify the endpoint that is being removed
        from the capture_listeners dictionary
        :return: The listener that was removed
        """
        if self.get_request_listener(endpoint):
            return self.capture_listeners.pop(endpoint.name)

    def clear_request_listeners(self) -> None:
        """
        The clear_request_listeners function clears the capture_listeners list.

        :param self: Represent the instance of the class
        :return: None
        """
        self.capture_listeners = None

    async def on_capture(self, endpoint: Endpoint, **kwargs) -> Any:
        """
        The on_capture function is called when a capture event occurs.

        :param self: Access the class attributes
        :param endpoint: Endpoint: Get the endpoint that is being called
        :param kwargs: Pass a dictionary of arguments to the function
        :return: The result of the call function
        """
        call: Callable = self.get_capture_listener(endpoint)
        if not call:
            return
        is_coro: bool = asyncio.iscoroutinefunction(call)
        if is_coro:
            return await call(**kwargs)
        return call(**kwargs)

    async def on_request(self, endpoint: Endpoint, response: Response) -> Any:
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


Listener = ListenerManager()
