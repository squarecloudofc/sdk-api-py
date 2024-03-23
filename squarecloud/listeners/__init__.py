import types
from inspect import Parameter
from typing import Callable, Union

from .. import data
from ..http.endpoints import Endpoint


class Listener:
    __slots__ = ('endpoint', 'callback', 'callback_args')

    def __init__(
        self,
        endpoint: Endpoint,
        callback: Callable,
        callback_args: types.MappingProxyType[str, Parameter],
    ):
        self.endpoint = endpoint
        self.callback = callback
        self.callback_args = callback_args

    def __repr__(self):
        return f'{self.__class__.__name__}(endpoint={self.endpoint})'


ListenerDataTypes = Union[
    data.AppData,
    data.StatusData,
    data.LogsData,
    data.BackupData,
]
