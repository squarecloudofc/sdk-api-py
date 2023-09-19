from __future__ import annotations

import io
import os
from typing import Any


class File:
    """
    File object

    You can use a file already opened or pass the file path.
    NOTE: To pass binary data, consider usage of `io.BytesIO`.
    """

    __slots__ = ('bytes', 'filename')

    def __init__(
        self,
        fp: str | bytes | os.PathLike[Any] | io.BufferedIOBase,
        filename: str | None = None,
    ):

        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and it's where you put all your
        initialization code.
        The __init__ function takes at least one argument: self, which refers
        to the object being created.

        :param self: Refer to the class instance
        :param fp: str | bytes | os.PathLike[Any] | io.BufferedIOBase: Define
        the file path,
        :param filename: str | None: Set the filename attribute of the class
        :return: None
        """
        if isinstance(fp, io.BufferedIOBase):
            if not (fp.seekable() and fp.readable()):
                raise ValueError(
                    f'File buffer {fp!r} must be seekable and readable'
                )
            self.bytes: io.BufferedIOBase = fp
        else:
            self.bytes = open(fp, 'rb')

        if filename is None:
            if isinstance(fp, str):
                _, filename = os.path.split(fp)
            else:
                filename = getattr(fp, 'name', None)

        self.filename: str | None = filename
