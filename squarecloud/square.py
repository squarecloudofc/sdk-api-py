"""module objects"""
from __future__ import annotations

import io
import os


class File:
    """File object"""
    __slots__ = (
        'path',
        'name',
        'bytes',
    )

    def __init__(self, path: str):
        self.bytes = io.open(path, 'rb')
        self.path = path
        self.name = os.path.basename(path)

    def __repr__(self):
        return f'<{self.__class__.__name__}(name={self.name}, path={self.path})'
