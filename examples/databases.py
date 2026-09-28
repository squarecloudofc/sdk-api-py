"""Create a Redis database, rotate its password, then delete it."""

import os

from squarecloud import SquareCloud

with SquareCloud(os.environ['SQUARECLOUD_API_KEY']) as client:
    db = client.databases.create('cache', type='redis', version='8', memory=512)
    try:
        print('created', db['id'], 'on', db['cluster'])  # db['password']: once
        print(client.databases.status(db['id'], raw=True))
        new_password = client.databases.reset_credentials(db['id'], 'password')
        print('password rotated:', bool(new_password))
    finally:
        client.databases.delete(db['id'])
