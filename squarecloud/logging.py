import logging

GREEN = '\033[0;32m'
PURPLE = '\033[0;35m'
RED = '\033[0;31m'
END = '\033[m'


class LogFormatter(logging.Formatter):
    """A custom logging formatter"""

    FORMAT_HTTP_LOGGER = '[%(levelname)s] - [HTTP] %(message)s'
    FORMAT_LISTENER_LOGGER = '[%(levelname)s] - [HTTP] %(message)s'

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
                format_body = self.FORMAT_HTTP_LOGGER
            case 'listener':
                format_body = self.FORMAT_LISTENER_LOGGER

        match record.levelname:
            case 'DEBUG':
                format_body = f'{GREEN}{format_body}{END}'
            case 'ERROR':
                format_body = f'{RED}{format_body}{END}'

        formatter = logging.Formatter(
            '\033[0;35m [%(asctime)s]\033[m ' + format_body
        )
        return formatter.format(record)


handler = logging.StreamHandler()
handler.setFormatter(LogFormatter())
logger = logging.getLogger('squarecloud')
logger.setLevel(logging.NOTSET)
logger.addHandler(handler)
