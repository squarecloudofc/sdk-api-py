"""Create a workspace, share an application with it, and act on the shared
application through its composite id.

Usage: python workspaces.py <app_id>
"""

import os
import sys

from squarecloud import SquareCloud

app_id = sys.argv[1]
with SquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client:
    ws = client.workspaces.create('team')
    try:
        client.workspaces.apps.add(ws['id'], app_id)
        shared = f'{app_id}-{ws["id"]}'  # The composite id of the shared application.
        print(client.apps.status(shared)['running'])
        print('share this code with an owner:', client.workspaces.members.invite_code())
        client.workspaces.apps.remove(ws['id'], app_id)
    finally:
        client.workspaces.delete(ws['id'])
