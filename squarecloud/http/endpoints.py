from __future__ import annotations


class Endpoint:
    """Endpoint"""

    ENDPOINTS_V2 = {
        'USER': {'METHOD': 'GET', 'PATH': '/user'},
        'APP_DATA': {'METHOD': 'GET', 'PATH': '/apps/{app_id}'},
        'APP_STATUS': {'METHOD': 'GET', 'PATH': '/apps/{app_id}/status'},
        'LOGS': {'METHOD': 'GET', 'PATH': '/apps/{app_id}/logs'},
        'START': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/start'},
        'STOP': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/stop'},
        'RESTART': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/restart'},
        'BACKUP': {'METHOD': 'GET', 'PATH': '/apps/{app_id}/backup'},
        'COMMIT': {'METHOD': 'POST', 'PATH': '/apps/{app_id}/commit'},
        'DELETE_APP': {'METHOD': 'DELETE', 'PATH': '/apps/{app_id}/delete'},
        'UPLOAD_APP': {'METHOD': 'POST', 'PATH': '/apps/upload'},
        'FILES_LIST': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/files/list?path={path}',
        },
        'FILES_READ': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/files/read?path={path}',
        },
        'FILES_CREATE': {
            'METHOD': 'POST',
            'PATH': '/apps/{app_id}/files/create',
        },
        'FILES_DELETE': {
            'METHOD': 'DELETE',
            'PATH': '/apps/{app_id}/files/delete?path={path}',
        },
        'LAST_DEPLOYS': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/deploy/list',
        },
        'GITHUB_INTEGRATION': {
            'METHOD': 'POST',
            'PATH': '/apps/{app_id}/deploy/git-webhook',
        },
        'CUSTOM_DOMAIN': {
            'METHOD': 'POST',
            'PATH': '/apps/{app_id}/network/custom/{custom_domain}',
        },
        'DOMAIN_ANALYTICS': {
            'METHOD': 'GET',
            'PATH': '/apps/{app_id}/network/analytics',
        },
    }

    def __init__(self, name: str) -> None:
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and defines its attributes.
        The __init__ function takes in a name parameter, which it uses to look
        up an endpoint from ENDPOINTS_V2.
        ENDPOINTS_V2 is a dictionary that contains all of our endpoints for
        version 2 of our API.

        :param self: Represent the instance of the class
        :param name: str: Set the name of the endpoint
        :return: None
        """
        if not (endpoint := self.ENDPOINTS_V2.get(name)):
            raise ValueError(f"Invalid endpoint: '{name}'")
        self.name: str = name
        self.method: str = endpoint['METHOD']
        self.path: str = endpoint['PATH']

    def __eq__(self, other: Endpoint):
        """
        The __eq__ function is used to compare two objects of the same class.
        It returns True if they are equal, and False otherwise.

        :param self: Refer to the current instance of the class
        :param other: Endpoint: Check if the other object is an instance of
        endpoint
        :return: A boolean value
        """
        return isinstance(other, Endpoint) and self.name == other.name

    def __repr__(self):
        """
        The __repr__ function is used to compute the &quot;official&quot;
        string representation of an object.
        This is how you would make an object of the class. The goal of

        :param self: Represent the instance of the class
        :return: A string that is the representation of an object
        """
        return f"{Endpoint.__name__}('{self.name}')"

    @classmethod
    def user(cls) -> Endpoint:
        """Returns an Endpoint object that represents the /user endpoint."""
        return cls('USER')

    @classmethod
    def app_data(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the /apps/{app_id} endpoint.
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
        /apps/{app_id}/backup endpoint.
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
        /apps/{app_id}/delete endpoint.
        """
        return cls('DELETE_APP')

    @classmethod
    def upload(cls) -> Endpoint:
        """
        Returns an Endpoint object that represents the
        /apps/upload endpoint.
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
    def last_deploys(cls):
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/deploy/list endpoint.
        """

        return cls('LAST_DEPLOYS')

    @classmethod
    def github_integration(cls):
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/deploy/git-webhook endpoint.
        """
        return cls('GITHUB_INTEGRATION')

    @classmethod
    def domain_analytics(cls):
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/network/analytics endpoint.
        """
        return cls('DOMAIN_ANALYTICS')

    @classmethod
    def custom_domain(cls):
        """
        Returns an Endpoint object that represents the
        /apps/{app_id}/network/custom/{custom_domain} endpoint.
        """
        return cls('CUSTOM_DOMAIN')


# pylint: disable=too-few-public-methods
class Router:
    """Represents a route"""

    # BASE_V1: str = 'https://api.squarecloud.app/v1/public'
    BASE_V2: str = 'https://api.squarecloud.app/v2'

    # noinspection StrFormat
    def __init__(self, endpoint: Endpoint, **params) -> None:
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

    def __repr__(self):
        """
        The __repr__ function is used to generate a string representation of
        an object.
        This function should return a printable representation of the object,
        and it will be used whenever you call str() on that object.

        :param self: Represent the instance of the class
        :return: A string that is a valid python expression
        """
        return f"{Router.__name__}(path='{self.path}', method='{self.method}')"
