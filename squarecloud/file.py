from __future__ import annotations

import io
import os
from typing import Any

from squarecloud import errors


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
    ) -> None:
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
            # Verificar se fp é bytes (dados binários) e criar um io.BytesIO
            if isinstance(fp, bytes):
                self.bytes = io.BytesIO(fp)
            else:
                self.bytes = open(fp, 'rb')

        if filename is None:
            if isinstance(fp, str):
                _, filename = os.path.split(fp)
            else:
                filename = getattr(fp, 'name', None)

        if not filename:
            raise errors.SquareException('You need provide a filename')

        self.filename: str | None = filename
