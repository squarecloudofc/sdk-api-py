from __future__ import annotations

from typing import Dict, Any


class Endpoint:
    BASE: str = 'https://api.squarecloud.app/v1/public'
    ENDPOINTS = {
        'USER_INFO': {'METHOD': 'GET', 'PATH': '/user'},
        'APP_STATUS': {'METHOD': 'GET', 'PATH': '/status/{app_id}'},
        'LOGS': {'METHOD': 'GET', 'PATH': '/logs/{app_id}'},
        'FULL_LOGS': {'METHOD': 'GET', 'PATH': '/full-logs/{app_id}'},
        'START': {'METHOD': 'POST', 'PATH': '/start/{app_id}'},
        'STOP': {'METHOD': 'POST', 'PATH': '/stop/{app_id}'},
        'RESTART': {'METHOD': 'POST', 'PATH': '/restart/{app_id}'},
        'BACKUP': {'METHOD': 'GET', 'PATH': '/backup/{app_id}'},
        'COMMIT': {'METHOD': 'POST', 'PATH': '/commit/{app_id}'},
        'DELETE': {'METHOD': 'POST', 'PATH': '/delete/{app_id}'},
        'UPLOAD': {'METHOD': 'POST', 'PATH': '/upload'},
    }

    def __init__(self, name: str):
        endpoint: Dict[str: Dict[str, Any]] = self.ENDPOINTS[name]
        self.name: str = name
        self.method: str = endpoint['METHOD']
        self.path: str = endpoint['PATH']

    def __repr__(self):
        return f"<{self.__class__.__name__}('{self.name}')>"

    @classmethod
    def user_info(cls):
        return cls('USER_INFO')

    @classmethod
    def app_status(cls):
        return cls('APP_STATUS')

    @classmethod
    def logs(cls):
        return cls('LOGS')

    @classmethod
    def full_logs(cls):
        return cls('FULL_LOGS')

    @classmethod
    def start(cls):
        return cls('START')

    @classmethod
    def stop(cls):
        return cls('STOP')

    @classmethod
    def restart(cls):
        return cls('RESTART')

    @classmethod
    def backup(cls):
        return cls('BACKUP')

    @classmethod
    def commit(cls):
        return cls('COMMIT')

    @classmethod
    def delete(cls):
        return cls('DELETE')

    @classmethod
    def upload(cls):
        return cls('UPLOAD')


class Router:
    """Represents a route"""
    BASE: str = 'https://api.squarecloud.app/v1/public'

    # noinspection StrFormat
    def __init__(self, endpoint: Endpoint, **params) -> None:
        self.endpoint: Endpoint = endpoint
        self.method: str = endpoint.method
        self.path: str = endpoint.path
        url: str = self.BASE + self.path.format(**params)
        if params:
            url.format(params)
        self.url = url
