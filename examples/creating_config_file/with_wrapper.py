from squarecloud.utils import ConfigFile

# BOT EXAMPLE
ConfigFile(
    display_name='an cool name',
    description='an cool description',
    main='main.py',
    memory=100,
    version='recommended',  # default 'recommended'
    auto_restart=False,  # default True
)

# WEBSITE EXAMPLE
ConfigFile(
    display_name='cool website',
    description='this is really cool',
    main='index.js',
    subdomain='cool-subdomain',
    start='start this cool website',  # if not static it is configurable
    memory=512,
    version='recommended',  # default 'recommended'
    auto_restart=False,  # default True
)


config = ConfigFile(*...)

# Saving file
config.save(
    'directory/to/save/'
)  # the path where the file should be saved, default='/'

# Serializing and Deserialization
config.to_dict()  # dict[str, Any]
config.content()  # str

ConfigFile.from_str(...)
ConfigFile.from_dict(...)


"""
[REQUIRED] parameters
---------------------
path: str
display_name: str
main: str
memory: int >= 100
version: Literal['recommended', 'latest']

[OPTIONAL] parameters
---------------------
description: str | None = None
subdomain: str | None = None
start: str | None = None
auto_restart: bool = False,
"""
