import inspect
import types
from typing import Any, Callable, Union

import pydantic
from pydantic import BaseModel

from .. import data, errors
from ..http import Endpoint
from . import Listener

ListenerDataTypes = Union[
    data.AppData,
    data.StatusData,
    data.LogsData,
    data.BackupData,
]


class CaptureListenerManager:
    """CaptureListenerManager"""

    def __init__(self):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance variables that will be used by other methods
        in the class.


        :param self: Refer to the class instance
        :return: A dictionary of the capture listeners and request listeners
        """
        self.capture_listeners: dict[str, Callable] = {}

    def get_listener(self, endpoint: Endpoint) -> Listener | None:
        """
        The get_listener function is used to get the capture listener
        for a given endpoint.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Get the capture listener from the endpoint
        name
        :return: The capture listener for the given endpoint
        """
        return self.capture_listeners.get(endpoint.name)

    def include_listener(self, endpoint: Endpoint, call: Callable) -> Listener:
        """
        The include_listener function adds a listener to the
        capture_listeners dictionary.
        The key is the name of an endpoint, and the value is a callable
        function that will be called when
        the endpoint's data has been captured.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Specify the endpoint that you want to
        listen to
        :param call: Callable: Define the function that will be called when a
        request is made to the endpoint
        :return: None
        """
        allowed_endpoints: tuple[Endpoint, Endpoint, Endpoint, Endpoint] = (
            Endpoint.logs(),
            Endpoint.app_status(),
            Endpoint.backup(),
            Endpoint.app_data(),
        )
        callback_args = inspect.signature(call).parameters
        listener = Listener(
            endpoint=endpoint,
            callback=call,
            callback_args=callback_args,
        )

        if endpoint not in allowed_endpoints:
            raise errors.InvalidListener(
                message='the endpoint to capture must be '
                f'{allowed_endpoints}',
                listener=call,
            )

        if self.get_listener(endpoint):
            raise errors.InvalidListener(
                message='Already exists an capture_listener for '
                f'{endpoint}',
                listener=call,
            )
        self.capture_listeners.update({endpoint.name: listener})
        return listener

    def remove_listener(self, endpoint: Endpoint) -> Callable:
        """
        The remove_capture_listener function removes a capture listener from
        the list of listeners.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Identify the endpoint to remove
        :return: The capture_listener that was removed from the dictionary
        """
        if self.get_listener(endpoint):
            return self.capture_listeners.pop(endpoint.name)

    def clear_capture_listeners(self) -> None:
        """
        The clear_capture_listeners function clears the capture_listeners list.

        :param self: Refer to the class instance
        :return: None
        """
        self.capture_listeners = None

    async def notify(
        self,
        endpoint: Endpoint,
        before: ListenerDataTypes | None,
        after: ListenerDataTypes,
        extra: Any = None,
    ) -> Any:
        """
        The on_capture function is called when a capture event occurs.

        :param self: Refer to the class instance
        :param endpoint: Endpoint: Get the endpoint that is being called
        :param before:
        :param after:
        :param extra:
        :return: The result of the call function
        """
        kwargs: dict[str, Any] = {}
        if not (listener_call := self.get_listener(endpoint)):
            return
        call_params = listener_call.callback_args
        if 'before' in call_params.keys():
            kwargs['before'] = before
        if 'after' in call_params.keys():
            kwargs['after'] = after
        if 'extra' in call_params.keys():
            kwargs['extra'] = extra

        call_extra_param: inspect.Parameter | None = call_params.get('extra')

        if call_extra_param:
            annotation: Any = call_extra_param.annotation

            if isinstance(annotation, types.UnionType):
                for ty in annotation.__args__:
                    if ty is None:
                        continue
                    if not issubclass(ty, BaseModel):
                        continue
                    try:
                        kwargs['extra'] = ty(**kwargs['extra'])
                        break
                    except pydantic.ValidationError:
                        continue
            else:
                if issubclass(annotation, BaseModel):
                    try:
                        kwargs['extra'] = call_extra_param.annotation(
                            **kwargs['extra']
                        )
                    except pydantic.ValidationError:
                        kwargs['extra'] = None

        is_coro: bool = inspect.iscoroutinefunction(listener_call.callback)
        if is_coro:
            return await listener_call.callback(**kwargs)
        return listener_call.callback(**kwargs)
