import asyncio
from functools import wraps

import click

from squarecloud import __version__


def run_async(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


@click.group()
@click.version_option(
    __version__, '--version', '-v', prog_name='squarecloud-api'
)
def cli():
    pass
