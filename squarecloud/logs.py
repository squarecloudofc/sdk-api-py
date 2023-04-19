"""Custom logger"""

import logging

# Define constants for color codes
GREEN = '\033[0;32m'
PURPLE = '\033[0;35m'
RED = '\033[0;31m'
END = '\033[m'

# logging config
logger = logging.getLogger(__name__)


class CustomLogFormatter(logging.Formatter):
    """A custom logging formatter"""

    FORMAT_SUCCESS = f'{GREEN}[%(levelname)s] %(status)s %(message)s %(route)s %(request_message)s {END}'
    FORMAT_ERROR = f'{RED}[%(levelname)s]  %(status)s %(message)s %(route)s, error: %(code)s{END}'

    def format(self, record: logging.LogRecord) -> str:
        if record.status == 'success':
            format_body = self.FORMAT_SUCCESS
        else:
            format_body = self.FORMAT_ERROR
        # log_fmt = PURPLE + format_body + END
        formatter = logging.Formatter(
            '\033[0;35m [%(asctime)s]: \033[m ' + format_body)
        return formatter.format(record)


# console handler
_ch = logging.StreamHandler()
_ch.setLevel(logging.DEBUG)
_ch.setFormatter(CustomLogFormatter())
logger.addHandler(_ch)
