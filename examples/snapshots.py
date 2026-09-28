"""Create an app snapshot, download it (once it is ready), and show how to
restore one.

usage: python snapshots.py <app_id>
"""

import os
import sys
import time

from squarecloud import SquareCloud

app_id = sys.argv[1]
with SquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client:
    known = {item['version_id'] for item in client.apps.snapshots.list(app_id)}
    snapshot = client.apps.snapshots.create(app_id)
    url = snapshot.get('url', '')
    while not url:
        # HTTP 202: it appears in list() within about 2 minutes. Never call
        # create() again: one per 180 s, and each call uses the daily quota.
        time.sleep(30)
        fresh = [
            item
            for item in client.apps.snapshots.list(app_id)
            if item['version_id'] not in known
        ]
        url = fresh[0]['url'] if fresh else ''
    print('saved to', client.download_snapshot(url, '.'))

    for item in client.apps.snapshots.list(app_id):
        print(item['name'], item['modified'], item['version_id'])
    # client.apps.snapshots.restore(app_id, item['name'], item['version_id'])
