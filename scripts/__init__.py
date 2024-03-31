import asyncio
from datetime import datetime
from typing import Callable

from rich.status import Status


def run_async_script(func: Callable):
    def wrapper(*args, **kwargs):
        with Status(f'Running {func.__name__}', spinner='point'):
            before = datetime.now()
            result = asyncio.run(func(*args, **kwargs))
            after = datetime.now()
            print(
                f'\u2713 Script ran successfully in '
                f'{(after - before).seconds} seconds!'
            )
            return result

    return wrapper
