import inspect
import types
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Optional, Type, Union

import pydantic
from pydantic import BaseModel

from .. import data, errors
from ..http.endpoints import Endpoint

if TYPE_CHECKING:
    from ..app import Application
    from ..client import Client


@dataclass(frozen=False)
class ListenerConfig:
    force_raise: bool = False


class Listener:
    __slots__ = (
        '_app',
        '_client',
        '_endpoint',
        '_callback',
        '_callback_params',
        'config',
    )

    def __init__(
        self,
        endpoint: Endpoint,
        callback: Callable,
        config: ListenerConfig = ListenerConfig(),
        app: Optional['Application'] = None,
        client: Optional['Client'] = None,
    ):
        self._app = app
        self._client = client
        self._endpoint = endpoint
        self._callback = callback
        self._callback_params = inspect.signature(callback).parameters
        self.config = config

    @property
    def app(self) -> 'Application':
        return self._app

    @property
    def endpoint(self) -> Endpoint:
        return self._endpoint

    @property
    def callback(self) -> Callable:
        return self._callback

    @property
    def callback_params(self) -> MappingProxyType[str, inspect.Parameter]:
        return self._callback_params

    def __repr__(self):
        return f'{self.__class__.__name__}(endpoint={self.endpoint})'


class ListenerManager:
    def __init__(self):
        """
        The __init__ method is called when the class is instantiated.
        It sets up the instance variables that will be used by other methods
        in the class.


        :param self: Refer to the class instance
        :return: A dictionary of the capture listeners and request listeners
        """
        self.listeners: dict[str, Callable] = {}

    def get_listener(self, endpoint: Endpoint) -> Listener | None:
        """
        The get_listener method is used to get the capture listener
        for a given endpoint.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Get the capture listener from the endpoint
        name
        :return: The capture listener for the given endpoint
        """
        return self.listeners.get(endpoint.name)

    def include_listener(self, listener: Listener) -> Listener:
        """
        The include_listener method adds a listener to the
        capture_listeners dictionary.
        The key is the name of an endpoint, and the value is a callable
        function that will be called when
        the endpoint's data has been captured.

        :param listener: the listener that will be included
        :param self: Refer to the class instance
        listen to
        request is made to the endpoint
        :return: None
        :raises InvalidListener: Raised if the endpoint is already registered
        """
        if self.get_listener(listener.endpoint):
            raise errors.InvalidListener(
                message='Already exists an capture_listener for '
                f'{listener.endpoint}',
                listener=listener.callback,
            )
        self.listeners.update({listener.endpoint.name: listener})
        return listener

    def remove_listener(self, endpoint: Endpoint) -> Callable:
        """
        The remove_listener method removes a capture listener from
        the list of listeners.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Identify the endpoint to remove
        :return: The capture_listener that was removed from the dictionary
        """
        if self.get_listener(endpoint):
            return self.listeners.pop(endpoint.name)

    def clear_listeners(self) -> None:
        """
        The clear_listeners function clears the capture_listeners list.

        :param self: Refer to the class instance
        :return: None
        """
        self.listeners = None

    @classmethod
    def cast_to_pydantic_model(
        cls, model: Type[BaseModel], values: dict[Any, Any]
    ):
        result: BaseModel | None | dict = values
        if isinstance(model, types.UnionType):
            for ty in model.__args__:
                if ty is None:
                    continue
                elif not issubclass(ty, BaseModel):
                    continue
                try:
                    a = ty(**values)
                    return a
                except pydantic.ValidationError:
                    continue
            return None
        if issubclass(model, BaseModel):
            try:
                result = model(**values)
            except pydantic.ValidationError as e:
                print(e)
                result = None
        return result


ListenerDataTypes = Union[
    data.AppData,
    data.StatusData,
    data.LogsData,
    data.BackupData,
]
