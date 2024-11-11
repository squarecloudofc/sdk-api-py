import logging

GREEN = '\033[1;32m'
BLUE = '\033[1;34m'
PURPLE = '\033[1;35m'
YELLOW = '\033[1;33m'
RED = '\033[1;31m'
END = '\033[m'


class LogFormatter(logging.Formatter):
    """A custom logging formatter"""

    HTTP = '[%(levelname)s] - [HTTP] %(message)s'
    LISTENER = '[%(levelname)s] - [LISTENER] %(message)s'

    def format(self, record: logging.LogRecord) -> str:
        """
        The format function is called by the logging system to format a log
        record.
        The function should return a string that will be used as the message
        of the log record.


        :param self: Refer to the class instance
        :param record: logging.LogRecord: Pass the log record to the format
        function
        :return: A string that will be used to format the log message
        """
        format_body: str = ''

        match record.__dict__.get('type'):
            case 'http':
                format_body = self.HTTP
            case 'listener':
                format_body = self.LISTENER

        match record.levelname:
            case 'DEBUG':
                format_body = f'{GREEN}{format_body}{END}'
            case 'INFO':
                format_body = f'{BLUE}{format_body}{END}'
            case 'ERROR':
                format_body = f'{RED}{format_body}{END}'
            case 'WARNING':
                format_body = f'{YELLOW}{format_body}{END}'

        formatter = logging.Formatter(
            f'{PURPLE}[%(asctime)s]{END} ' + format_body
        )
        return formatter.format(record)


handler = logging.StreamHandler()
handler.setFormatter(LogFormatter())
logger = logging.getLogger('squarecloud')
logger.setLevel(logging.NOTSET)
logger.addHandler(handler)
