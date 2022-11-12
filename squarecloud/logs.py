"""custom logger"""
import logging

# logging config
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CustomFormatter(logging.Formatter):
    """a custom logging formatter"""
    green = '\033[0;32m'
    purple = '\033[0;35m'
    red = '\033[0;31m'
    end = '\033[m'

    FORMAT_SUCCESS = f'{green}[%(levelname)s] %(status)s %(message)s [%(route)s] %(request_message)s {end}'
    FORMAT_ERROR = f'{red}[%(levelname)s]  %(status)s %(message)s %(route)s, error: %(code)s{end}'

    def format(self, record: logging.LogRecord) -> str:
        if record.status == 'success':
            format_body = self.FORMAT_SUCCESS
        else:
            format_body = self.FORMAT_ERROR
        # formats_level = {
        #     logging.INFO: self.purple + format_body + self.end,
        #     logging.DEBUG: self.green + format_body + self.end,
        #     logging.ERROR: self.red + format_body + self.end,
        #     logging.CRITICAL: self.red + format_body + self.end,
        #     logging.WARN: self.red + format_body + self.end,
        # }
        # log_fmt = formats_level.get(record.levelno)
        # log_fmt = self.purple + format_body + self.end
        formatter = logging.Formatter('\033[0;35m [%(asctime)s]: \033[m ' + format_body)
        return formatter.format(record)


# console handler
_ch = logging.StreamHandler()
_ch.setLevel(logging.DEBUG)
_ch.setFormatter(CustomFormatter())
logger.addHandler(_ch)
