"""Upload an app, commit an update, edit files and envs, and link a GitHub
repository through the Square Cloud GitHub App.

usage: python apps.py app.zip [owner/repo branch]
"""

import os
import sys

from squarecloud import SquareCloud, SquareCloudAPIError

with SquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client:
    app = client.apps.create(sys.argv[1])  # streamed from disk
    print('created', app['id'], app.get('domain'))  # a website's host

    client.apps.commit(app['id'], b'console.log("hi")\n', filename='hello.js')
    client.apps.files.write(app['id'], '/NOTES.txt', 'deployed by the SDK\n')
    client.apps.files.write(app['id'], '/blob.bin', bytes(range(256)))  # base64
    assert client.apps.files.read(app['id'], '/blob.bin') == bytes(range(256))
    print([f['name'] for f in client.apps.files.list(app['id'])])
    client.apps.envs.set(app['id'], {'NODE_ENV': 'production'})
    client.apps.restart(app['id'])

    if len(sys.argv) > 3:  # needs the GitHub App installed on the repository
        try:
            linked = client.apps.deploys.link_github_app(
                app['id'], sys.argv[2], sys.argv[3]
            )
            print('linked', linked['full_name'], linked['branch'])
            print(client.apps.deploys.current(app['id']))
            client.apps.deploys.unlink_github_app(app['id'])
        except SquareCloudAPIError as e:
            print('GitHub App:', e.code, e.message)
