"""Follow an app's logs and metrics live (Ctrl+C to stop).

usage: python realtime.py <app_id>
"""

import os
import sys

from squarecloud import SquareCloud

with (
    SquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client,
    client.apps.realtime(sys.argv[1]) as stream,
):
    for event in stream:
        if event['event'] == 'logs':
            print(f'[{event["stream"]}] {event["line"]}')
        elif event['event'] == 'status':
            status = event['status']
            print(f'cpu={status.get("cpu")} ram={status.get("ram")}')
        else:
            print(event['event'], event['data'])
