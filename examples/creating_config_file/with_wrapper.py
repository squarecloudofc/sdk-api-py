import squarecloud as square

# BOT EXAMPLE
square.create_config_file(
    path='directory/to/save/',  # the path where the file should be saved
    display_name='an cool name',
    description='an cool description',
    main='main.py',
    memory=100,
    version='recommended',
)

# WEBSITE EXAMPLE
square.create_config_file(
    path='directory/to/save',
    display_name='cool website',
    description='this is really cool',
    main='index.js',
    subdomain='coolwebsite.squareweb.app',
    start='start this cool website',  # if not static it is configurable
    memory=512,
    version='recommended',
    auto_restart=False,
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
auto_restart: bool = False,
"""
