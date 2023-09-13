from io import BufferedReader

import click
from click import Context
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import squarecloud
from squarecloud import Client
from squarecloud.app import Application
from squarecloud.cli import cli, run_async
from squarecloud.data import (
    AppData,
    BackupData,
    LogsData,
    StatusData,
    UploadData,
)


@cli.group(
    name='app',
    invoke_without_command=True,
    help='Manage your applications',
)
@click.argument(
    'app_id',
    type=click.STRING,
    required=False,
)
@click.option(
    '--token',
    '-t',
    help='your api token',
    envvar='SQUARECLOUD-TOKEN',
    required=True,
    type=click.STRING,
    prompt='API KEY',
    hide_input=True,
)
@click.pass_context
@run_async
async def app_group(ctx: Context, app_id: str, token: str):
    if not app_id:
        click.echo(ctx.get_help())
        return
    client = Client(token, debug=False)
    if not ctx.invoked_subcommand:
        with Console().status('loading'):
            app = await client.app(app_id)
            table = Table(title=app.tag, header_style='purple')
            table.add_column('Tag', justify='center')
            table.add_column('ID', justify='center')
            table.add_column('Type', justify='center')
            table.add_column('RAM', justify='center')
            table.add_column('Language', justify='center')
            table.add_column('Description', justify='center')
            table.add_column('Is Website', justify='center')
            table.add_column('Avatar', justify='center')
            table.add_column('Cluster', justify='center')

            table.add_row(
                app.tag,
                app.id,
                app.type,
                str(app.ram),
                app.lang,
                app.desc,
                str(app.is_website),
                app.avatar,
                app.cluster,
                style='green',
            )
        print(table)
        return
    ctx.ensure_object(dict)
    ctx.obj['app_id'] = app_id
    ctx.obj['token'] = token
    ctx.obj['client'] = client


@app_group.command('status', help='Get the application status')
@click.pass_context
@run_async
async def get_app_status(ctx: Context):
    client: Client = ctx.obj['client']
    app_id = ctx.obj['app_id']
    with Console().status('loading'):
        status: StatusData = await client.app_status(app_id)

        table = Table(title='Status', header_style='purple')

        status_list = [
            attr for attr in dir(status) if not attr.startswith('__')
        ]
        for s in status_list:
            table.add_column(s.capitalize(), justify='center')
        table.add_row(
            *[str(getattr(status, attr)) for attr in status_list],
            style='green',
        )
    print(table)


@click.command(name='app-list', help='Get a list of all applications')
@click.option(
    '--token',
    '-t',
    help='your api token',
    envvar='SQUARECLOUD-TOKEN',
    required=True,
    type=click.STRING,
    prompt='API KEY',
    hide_input=True,
)
@click.pass_context
@run_async
async def app_list(ctx: Context, token: str):
    client = Client(token, debug=False)
    with Console().status('loading'):
        apps: list[Application] = await client.all_apps()
    if not apps:
        print(
            Panel(
                f'You do not have any application',
                title_align='left',
                style='red',
            ),
        )
        return
    table = Table(title='App List', header_style='purple')

    table.add_column('Tag', justify='center')
    table.add_column('ID', justify='center')
    table.add_column('Type', justify='center')
    table.add_column('RAM', justify='center')
    table.add_column('Language', justify='center')
    table.add_column('Description', justify='center')
    table.add_column('Is Website', justify='center')
    table.add_column('Avatar', justify='center')
    table.add_column('Cluster', justify='center')
    for app in apps:
        table.add_row(
            app.tag,
            app.id,
            app.type,
            str(app.ram),
            app.lang,
            app.desc,
            str(app.is_website),
            app.avatar,
            app.cluster,
            style='green',
        )
    print(table)


@app_group.command(name='data', help='Get the application data')
@click.pass_context
@run_async
async def app_data(ctx: Context):
    client: Client = ctx.obj['client']
    app_id = ctx.obj['app_id']
    with Console().status('loading'):
        data: AppData = await client.app_data(app_id)
        table = Table(title='Status', header_style='purple')

        status_list = [attr for attr in dir(data) if not attr.startswith('__')]
        for s in status_list:
            table.add_column(s.capitalize(), justify='center')
        table.add_row(
            *[str(getattr(data, attr)) for attr in status_list],
            style='green',
        )

    print(table)


@app_group.command(name='logs', help='Get logs of the application')
@click.pass_context
@run_async
async def app_logs(ctx: Context):
    client: Client = ctx.obj['client']
    app_id = ctx.obj['app_id']
    with Console().status('loading'):
        logs: LogsData = await client.get_logs(app_id)
        panel = Panel(
            logs.logs,
            title='Logs',
            title_align='left',
            style='green',
            border_style='purple',
        )
    print(panel)


@app_group.command(name='backup', help='Backup the application')
@click.pass_context
@run_async
async def app_backup(ctx: Context):
    client: Client = ctx.obj['client']
    app_id = ctx.obj['app_id']
    with Console().status('loading'):
        backup: BackupData = await client.backup(app_id)
        panel = Panel(
            backup.downloadURL,
            title='Backup URL',
            title_align='left',
            style='green',
            border_style='purple',
        )
    print(panel)


@app_group.command(name='start', help='Start the application')
@click.pass_context
@run_async
async def start_app(ctx: Context):
    client: Client = ctx.obj['client']
    app_id = ctx.obj['app_id']
    with Console().status('loading'):
        await client.start_app(app_id)
        panel = Panel(
            f'Application with id {app_id} has been started',
            title='App started',
            title_align='left',
            style='green',
            border_style='purple',
        )
    print(panel)


@app_group.command(name='stop', help='Stop the application')
@click.pass_context
@run_async
async def stop_app(ctx: Context):
    client: Client = ctx.obj['client']
    app_id = ctx.obj['app_id']
    with Console().status('loading'):
        await client.stop_app(app_id)
        panel = Panel(
            f'Application with id {app_id} has been stopped',
            title='App stopped',
            title_align='left',
            style='red',
            border_style='purple',
        )
    print(panel)


@app_group.command(name='restart', help='Stop the application')
@click.pass_context
@run_async
async def restart_app(ctx: Context):
    client: Client = ctx.obj['client']
    app_id = ctx.obj['app_id']
    with Console().status('loading'):
        await client.restart_app(app_id)
        panel = Panel(
            f'Application with id {app_id} has been restarted',
            title='App restarted',
            title_align='left',
            style='yellow',
            border_style='purple',
        )
    print(panel)


@app_group.command(name='delete', help='Delete a application')
@click.confirmation_option(
    prompt='Are you sure you want to delete this application?',
)
@click.pass_context
@run_async
async def start_app(ctx: Context):
    client: Client = ctx.obj['client']
    app_id = ctx.obj['app_id']
    with Console().status('loading'):
        await client.delete_app(app_id)
        panel = Panel(
            f'Application with id {app_id} has been deleted',
            title='App deleted',
            title_align='left',
            style='red',
            border_style='purple',
        )
    print(panel)


@cli.command(name='upload', help='Upload a new application')
@click.argument(
    'file',
    type=click.File('rb'),
    required=True,
)
@click.option(
    '--token',
    '-t',
    help='your api token',
    envvar='SQUARECLOUD-TOKEN',
    required=True,
    type=click.STRING,
    prompt='API KEY',
    hide_input=True,
)
@run_async
async def upload_app(token: str, file: BufferedReader):
    client = Client(token, debug=False)
    with Console().status('loading'):
        upload_data: UploadData = await client.upload_app(
            file=squarecloud.File(file)
        )
        panel = Panel(
            f'Application with id {upload_data.id} has been uploaded',
            title='App uploaded',
            title_align='left',
            style='green',
            border_style='purple',
        )
    print(panel)


@app_group.command(name='commit', help='Commit a file to an application')
@click.argument('file', type=click.File('rb'))
@click.pass_context
@run_async
async def commit(ctx: Context, file: BufferedReader):
    with Console().status('loading'):
        client: Client = ctx.obj['client']
        app_id = ctx.obj['app_id']
        await client.commit(app_id, squarecloud.File(file))
    print(
        Panel(
            f'File {file.name} has been committed to app with id {app_id}',
            border_style='purple',
            style='green',
        )
    )
