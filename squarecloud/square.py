"""module objects"""
from __future__ import annotations

import os
from abc import ABC
from typing import Literal, TYPE_CHECKING

from .data import AppData

# avoid circular imports
if TYPE_CHECKING:
    from .client import Client


class File:
    __slots__ = (
        'path',
        'name',
        'file',
    )
    """File object"""

    def __init__(self, path: str):
        self.file = open(path, 'rb')
        self.path = path
        self.name = os.path.basename(path)


class AbstractApplication(ABC):
    """Abstract application class"""


class Application(AbstractApplication):
    """Represents an application"""
    # pylint: disable=too-many-instance-attributes
    # nine arguments is available in this case
    # pylint: disable=invalid-name
    __slots__ = [
        '__client',
        '__id',
        '__tag',
        '__ram',
        '__lang',
        '__type',
        '__cluster',
        '__is_website',
        '__avatar',
    ]

    def __init__(self, client: 'Client', data: AppData):
        self.__client: 'Client' = client
        self.__id: int | str = data.id
        self.__tag: str = data.tag
        self.__ram: int = data.ram
        self.__lang: Literal['javascript', 'typescript', 'python'] = data.lang
        self.__type: Literal['free', 'paid'] = data.type
        self.__cluster: str = data.cluster
        self.__is_website: bool = data.isWebsite
        self.__avatar: str = data.avatar

    def __repr__(self):
        return f'<{self.__class__.__name__} id={self.id} tag={self.tag}>'

    @property
    def client(self):
        """client instance"""
        return self.__client

    @property
    def id(self):
        """application's id"""
        return self.__id

    @property
    def tag(self):
        """application's tag"""
        return self.__tag

    @property
    def ram(self):
        """application's allocated ram"""
        return self.__ram

    @property
    def lang(self):
        """application's programing language"""
        return self.__lang

    @property
    def type(self):
        """application's type"""
        return self.__type

    @property
    def cluster(self):
        """application's cluster"""
        return self.__cluster

    @property
    def is_website(self):
        """whether the application is a website"""
        return self.__is_website

    @property
    def avatar(self):
        """application's avatar"""
        return self.__avatar
#
# class Logs:
#     def __init__(self, Logs: Log):
#         self._logs:
