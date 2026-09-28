"""The same API with await: statuses of every app and database at once."""

import asyncio
import os

from squarecloud import AsyncSquareCloud


async def main() -> None:
    async with AsyncSquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client:
        apps, databases, workspaces = await asyncio.gather(
            client.apps.status_all(),
            client.databases.status_all(),
            client.workspaces.list(),
        )
        print(len(apps), 'apps,', len(databases), 'databases')
        for ws in workspaces:
            for app in ws['applications']:
                shared_id = f'{app["id"]}-{ws["id"]}'  # act on a shared app
                print(
                    ws['name'],
                    app['name'],
                    (await client.apps.status(shared_id))['status'],
                )


asyncio.run(main())
