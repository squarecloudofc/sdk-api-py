import click
from dotenv import load_dotenv
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from squarecloud.client import Client
from squarecloud.data import StatisticsData
from . import run_async, cli
from .app import app_group
from .. import RequestError

load_dotenv()

__version__ = '3.1.0'


@cli.command(name='statistics')
@click.option(
    '--token',
    '-t',
    help='your api token',
    envvar='SQUARECLOUD-TOKEN',
    required=True,
    type=click.STRING,
    prompt='API KEY',
    hide_input=True
)
@run_async
async def get_squarecloud_statistics(token: str):
    client = Client(api_key=token, debug=False)

    with Console().status('loading') as status:
        statistics_data: StatisticsData = await client.statistics()
    table = Table(title='Statistics', header_style='purple')

    table.add_column('Apps', justify='center')
    table.add_column('Websites', justify='center')
    table.add_column('Time', justify='center')
    table.add_column('Ping', justify='center')
    table.add_column('Users', justify='center')

    table.add_row(
        str(statistics_data.apps),
        str(statistics_data.websites),
        str(statistics_data.time),
        str(statistics_data.ping),
        str(statistics_data.users),
        style='green'
    )
    print(table)


cli.add_command(app_group)


def safe_entry_point():
    try:
        cli()
    except RequestError as e:
        title = e.__class__.__name__
        print(Panel(e.message, title=title, title_align='left', style='red'))
