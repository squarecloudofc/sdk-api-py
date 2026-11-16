"""Take a snapshot of an application and download it once it is ready.

With --restore, also restore the newest snapshot and follow the restore
until it ends.

Usage: python snapshots.py <app_id> [--restore]
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
        # The snapshot is still being generated and appears in list() within
        # about 2 minutes. Do not call create() again, because it allows one
        # call every 180 seconds and each call counts against the daily quota.
        time.sleep(30)
        fresh = [
            item
            for item in client.apps.snapshots.list(app_id)
            if item['version_id'] not in known
        ]
        url = fresh[0]['url'] if fresh else ''
    print('saved to', client.download_snapshot(url, '.'))  # Valid for 1 hour.

    latest = max(client.apps.snapshots.list(app_id), key=lambda s: s['modified'])
    print(latest['name'], latest['modified'], latest['version_id'])
    if '--restore' in sys.argv:  # Replaces the application's files.
        snapshots = client.apps.snapshots
        restored = snapshots.restore(app_id, latest['name'], latest['version_id'])
        if restored['pending']:
            # The restore keeps running. Do not call restore() again. Follow
            # it with restore_state(), which allows 30 calls a minute.
            state = snapshots.restore_state(app_id)
            while state['state'] in ('queued', 'running'):
                print('restoring:', state.get('step', state['state']))
                time.sleep(5)
                state = snapshots.restore_state(app_id)
            print('restore:', state['state'], state.get('code', ''))
        else:
            print('restore: success')
