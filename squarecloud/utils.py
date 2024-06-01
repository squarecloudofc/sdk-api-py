from typing import Any, Literal


class ConfigFile:
    """
    This object represents a configuration file.
    You can see more of this file in the official documentation:
    https://docs.squarecloud.app/articles/how-to-create-your-squarecloud-configuration-file
    """

    def __init__(
        self,
        display_name: str,
        main: str,
        memory: int,
        version: Literal['recommended', 'latest'] = 'recommended',
        description: str | None = None,
        subdomain: str | None = None,
        start: str | None = None,
        auto_restart: bool = False,
    ) -> None:
        if version not in ('latest', 'recommended'):
            raise ValueError('Invalid version')
        if memory < 256:
            raise ValueError('Memory must be greater than 256MB')
        elif memory < 512 and subdomain:
            raise ValueError('Websites memory must be grater than 512MB')
        self.display_name = display_name
        self.main = main
        self.memory = memory
        self.version = version
        self.description = description
        self.subdomain = subdomain
        self.start = start
        self.auto_restart = auto_restart

    def __repr__(self) -> str:
        """Return a string representation of the config file content"""
        return f"""{self.__class__.__name__}(\n{self.content()}\n)"""

    @classmethod
    def from_str(cls, content: str) -> 'ConfigFile':
        """Returns a class from a file content string"""
        output: dict = {}
        for line in content.splitlines():
            if '=' not in line:
                continue
            key, value = line.split('=')
            if value.isdigit():
                value = int(value)
            output.update({key.lower(): value})
        return cls(**output)

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> 'ConfigFile':
        return cls(**dictionary)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    def content(self) -> str:
        content = ''
        for key, value in self.__dict__.items():
            if value:
                string: str = f'{key.upper()}={value}\n'
                content += string
        return '\n'.join(content.splitlines())

    def save(self, path: str = '') -> None:
        content = self.content()
        with open(f'./{path}/squarecloud.app', 'w', encoding='utf-8') as file:
            file.write(content)
