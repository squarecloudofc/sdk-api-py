import asyncio
from typing import Callable

from .http import Response
from .http.endpoints import Endpoint


class ListenerManager:
    def __init__(self):
        self.capture_listeners: dict[str, Callable] = {}
        self.request_listeners: dict[str, Callable] = {}

    def get_capture_listener(self, endpoint: Endpoint):
        return self.capture_listeners.get(endpoint.name)

    def add_capture_listener(self, endpoint: Endpoint, call: Callable):
        if not self.get_capture_listener(endpoint):
            return self.capture_listeners.update({endpoint.name: call})

    def remove_capture_listener(self, endpoint: Endpoint):
        if self.get_capture_listener(endpoint):
            return self.capture_listeners.pop(endpoint.name)

    def clear_capture_listeners(self):
        self.capture_listeners = None

    def get_request_listener(self, endpoint: Endpoint):
        return self.request_listeners.get(endpoint.name)

    def add_request_listener(self, endpoint: Endpoint, call: Callable):
        if not self.get_request_listener(endpoint):
            return self.request_listeners.update({endpoint.name: call})

    def remove_request_listener(self, endpoint: Endpoint):
        if self.get_request_listener(endpoint):
            return self.capture_listeners.pop(endpoint.name)

    def clear_request_listeners(self):
        self.capture_listeners = None

    async def on_capture(self, endpoint: Endpoint, **kwargs):
        call: Callable = self.get_capture_listener(endpoint)
        if not call:
            return
        is_coro: bool = asyncio.iscoroutinefunction(call)
        if is_coro:
            return await call(**kwargs)
        return call(**kwargs)

    async def on_request(self, endpoint: Endpoint, response: Response):
        call: Callable = self.get_request_listener(endpoint)
        if not call:
            return
        if asyncio.iscoroutinefunction(call):
            return await call(response=response)
        return call(response=response)


Listener = ListenerManager()
