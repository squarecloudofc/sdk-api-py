from __future__ import annotations


class Endpoint:
    """Class representing an API endpoint."""

    ENDPOINTS_V2 = {
        'USER': {'METHOD': 'GET', 'PATH': '/users/me'},
        'APP_DATA': {'METHOD': 'GET', 'PATH': '/apps/{app_id}'},
        'APP_STATUS': {'METHOD': 'GET', 'PATH': '/apps/{app_id}/status'},
        'ALL_APPS_STATUS': {'METHOD': 'GET', 'PATH': '/apps/status'},
        'ALL_BACKUPS': {'METHOD': 'GET', 'PATH': '/apps/{app_id}/backups'},
        'LOGS': {'METHOD': 'GET', 'PATH': '/apps/{app_id}/logs'},
        'START': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/start'},
        'STOP': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/stop'},
        'RESTART': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/restart'},
        'BACKUP': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/backups'},
        'COMMIT': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/commit'},
        'DELETE_APP': {'METHOD': 'DELETE', 'PATH': '/apps/{app_id}'},
        'UPLOAD_APP': {'METHOD': 'POST', 'PATH': '/apps'},
        'FILES_LIST': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/files?path={path}',
        },
        'FILES_READ': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/files/content?path={path}',
        },
        'FILES_CREATE': {
            'METHOD': 'PUT',
            'PATH': '/apps/{app_id}/files',
        },
        'FILES_DELETE': {
            'METHOD': 'DELETE',
            'PATH': '/apps/{app_id}/files',
        },
        'MOVE_FILE': {'METHOD': 'PATCH', 'PATH': '/apps/{app_id}/files'},
        'LAST_DEPLOYS': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/deployments',
        },
        'CURRENT_INTEGRATION': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/deployments/current',
        },
        'GITHUB_INTEGRATION': {
            'METHOD': 'POST',
            'PATH': '/apps/{app_id}/deploy/webhook',
        },
        'CUSTOM_DOMAIN': {
            'METHOD': 'POST',
            'PATH': '/apps/{app_id}/network/custom',
        },
        'DOMAIN_ANALYTICS': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/network/analytics',
        },
        'DNSRECORDS': {'METHOD': 'GET', 'PATH': '/apps/{app_id}/network/dns'},
    }

    def __init__(self, name: str) -> None:
        """
        Initialize an Endpoint instance with the given name.

        :param name: The name of the endpoint.
        :raises ValueError: If the endpoint name is invalid.
        """
        if not (endpoint := self.ENDPOINTS_V2.get(name)):
            raise ValueError(f"Invalid endpoint: '{name}'")
        self.name: str = name
        self.method: str = endpoint['METHOD']
        self.path: str = endpoint['PATH']

    def __eq__(self, other: object) -> bool:
        """
        Compare two Endpoint instances for equality.

        :param other: The other Endpoint instance to compare.
        :return: True if both instances have the same name, otherwise False.
        """
        return isinstance(other, Endpoint) and self.name == other.name

    def __repr__(self) -> str:
        """
        Return the official string representation of the Endpoint instance.

        :return: A string representation of the Endpoint instance.
        """
        return f"{Endpoint.__name__}('{self.name}')"

    @classmethod
    def user(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /user endpoint.
        """
        return cls('USER')

    @classmethod
    def app_data(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id} endpoint.
        """
        return cls('APP_DATA')

    @classmethod
    def app_status(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/status endpoint.
        """
        return cls('APP_STATUS')

    @classmethod
    def logs(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/logs endpoint.
        """
        return cls('LOGS')

    @classmethod
    def start(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/start endpoint.
        """
        return cls('START')

    @classmethod
    def stop(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/stop endpoint.
        """
        return cls('STOP')

    @classmethod
    def restart(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/restart endpoint.
        """
        return cls('RESTART')

    @classmethod
    def backup(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/backups endpoint.
        """
        return cls('BACKUP')

    @classmethod
    def commit(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/commit endpoint.
        """
        return cls('COMMIT')

    @classmethod
    def delete_app(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id} endpoint.
        """
        return cls('DELETE_APP')

    @classmethod
    def upload(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps endpoint.
        """
        return cls('UPLOAD_APP')

    @classmethod
    def files_list(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/files/list endpoint.
        """
        return cls('FILES_LIST')

    @classmethod
    def files_read(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/files/read endpoint.
        """
        return cls('FILES_READ')

    @classmethod
    def files_create(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/files/create endpoint.
        """
        return cls('FILES_CREATE')

    @classmethod
    def files_delete(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/files/delete endpoint.
        """
        return cls('FILES_DELETE')

    @classmethod
    def last_deploys(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/deployments endpoint.
        """
        return cls('LAST_DEPLOYS')

    @classmethod
    def github_integration(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/deploy/webhook endpoint.
        """
        return cls('GITHUB_INTEGRATION')

    @classmethod
    def domain_analytics(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/network/analytics endpoint.
        """
        return cls('DOMAIN_ANALYTICS')

    @classmethod
    def custom_domain(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/network/custom endpoint.
        """
        return cls('CUSTOM_DOMAIN')

    @classmethod
    def all_backups(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/backups endpoint.
        """
        return cls('ALL_BACKUPS')

    @classmethod
    def all_apps_status(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/status endpoint.
        """
        return cls('ALL_APPS_STATUS')

    @classmethod
    def current_integration(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/deployments/current endpoint.
        """
        return cls('CURRENT_INTEGRATION')

    @classmethod
    def move_file(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/files
        """
        return cls('MOVE_FILE')

    @classmethod
    def dns_records(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/network/dns
        """
        return cls('DNSRECORDS')


# pylint: disable=too-few-public-methods
class Router:
    """Represents a route"""

    # BASE_V1: str = 'https://api.squarecloud.app/v1/public'
    BASE_V2: str = 'https://api.squarecloud.app/v2'

    # noinspection StrFormat
    def __init__(self, endpoint: Endpoint, **params: str | int) -> None:
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and it's where you define your
        attributes.


        :param self: Represent the instance of the class
        :param endpoint: Endpoint: Define the endpoint
        :param **params: Pass in the parameters for the url
        :return: None
        """
        self.endpoint: Endpoint = endpoint
        self.method: str = endpoint.method
        self.path: str = endpoint.path
        url: str = self.BASE_V2 + self.path.format(**params)
        if params:
            url.format(params)
        self.url = url

    def __repr__(self) -> str:
        """
        The __repr__ function is used to generate a string representation of
        an object.
        This function should return a printable representation of the object,
        and it will be used whenever you call str() on that object.

        :param self: Represent the instance of the class
        :return: A string that is a valid python expression
        """
        return f"{Router.__name__}(path='{self.path}', method='{self.method}')"
