# How I can make commits and uploads?

you can commit & upload using a [client](client.md) or
an [application](application.md),
you will just need a `square.File` object passing the path to where your
zip/unique file is located.

## Making a Commit:

- ### with [Client](client.md):

```python
import squarecloud as square

client = square.Client(...)


async def example():
    file = square.File('path/to/you/file.zip')
    await client.commit(file=file, app_id='abcdxyz')
```

- ### with [Application](application.md):

```python
import squarecloud as square

client = square.Client(...)


async def example():
    app = await client.app(app_id='abcdxyz')
    file = square.File('path/to/you/file.zip')
    await app.commit(file=file)
```

___

## Making a Upload:

to upload an application you only use the client

```python
import squarecloud as square

client = square.Client(...)


async def example():
    file = square.File('path/to/you/file.zip')
    await client.upload_app(file=file)
```

**remembering that to upload an application you need a zip that contains (at
least) the following files**:

- main file: responsible for starting your bot
- dependencies file: contains information about which dependencies are required
- config file(squarecloud.app): a configuration file specifying name,
  description, main file name, version, etc. To know more about the
  configuration file take a look at [this guide](https://docs.squarecloud.app/suporte/como-hospedar#configurando-sua-aplicacao)

for your convenience a function was added to create the configuration file:

```python
import squarecloud as square

# application example
square.create_config_file(
    path='directory/to/save/', # the path where the file should be saved
    display_name='an cool name',
    description='an cool description',
    main='main.py',
    memory=100,
    version='recommended',
)

# website example
square.create_config_file(
    path='directory/to/save',
    display_name='cool website',
    description='this is really cool',
    main='index.js',
    subdomain='coolwebsite.squareweb.app',
    start='start this cool website', # if not static it is configurable
    memory=512,
    version='recommended',
)

"""
[REQUIRED] parameters
---------------------
path: str
display_name: str
main: str
memory: int
version: Literal['recommended', 'latest']

[OPTIONAL] parameters
---------------------
avatar: str | None = None
description: str | None = None
subdomain: str | None = None
start: str | None = None
"""
```
