import inspect
import logging

from colorama import Back, Fore, Style
from verboselogs import VerboseLogger

logging.setLoggerClass(VerboseLogger)

CHECKMARK = f"{Style.BRIGHT}{Back.GREEN}\u2713{Style.NORMAL}{Back.RESET}"


def freeze_logging(func):
    """Decorator to set the logging pathname, filename, and lineno based on the caller of the decorated function."""

    class CustomLogRecord(logging.LogRecord):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Capture the stack frame of the caller outside the current module and not from __init__.py
            for f in inspect.stack():
                if (
                    f[1] != inspect.getfile(inspect.currentframe())
                    and "__init__.py" not in f[1]
                    and "utils.py" not in f[1]
                ):
                    self.pathname = f[1]
                    self.filename = f[1].split("/")[-1]
                    self.lineno = f[2]
                    break
            else:
                self.pathname = "unknown_path"
                self.lineno = 0

    def wrapper(*args, **kwargs):
        # Temporarily replace the LogRecord class for the logger
        original_factory = logging.getLogRecordFactory()
        logging.setLogRecordFactory(CustomLogRecord)

        try:
            return func(*args, **kwargs)
        finally:
            # Restore the original LogRecord class
            logging.setLogRecordFactory(original_factory)

    return wrapper


def auditor_logger(name: str):
    logger = logging.getLogger(name)
    logger = AuditorAdapter(logger)
    return logger


def local_logger(name: str):
    logger = logging.getLogger(name)
    logger = LocalAdapter(logger)
    return logger


def assert_logger(name: str):
    logger = logging.getLogger(name)
    logger = AssertAdapter(logger)
    return logger


def data_logger(name: str):
    logger = logging.getLogger(name)
    logger = DataAdapter(logger)
    return logger


class DataAdapter(logging.LoggerAdapter):
    """
    Wrap all messages with "data: " and make the message green.
    """

    def process(self, msg, kwargs):
        return f"{Fore.GREEN}data: {msg}{Style.RESET_ALL}", kwargs

    @freeze_logging
    def verbose(self, msg, *args, **kwargs):
        self.log(logging.VERBOSE, msg, *args, **kwargs)

    @freeze_logging
    def notice(self, msg, *args, **kwargs):
        self.log(logging.NOTICE, msg, *args, **kwargs)

    @freeze_logging
    def success(self, msg, *args, **kwargs):
        self.log(logging.SUCCESS, msg, *args, **kwargs)

    @freeze_logging
    def spam(self, msg, *args, **kwargs):
        self.log(logging.SPAM, msg, *args, **kwargs)

    @freeze_logging
    def failure(self, msg, *args, **kwargs):
        self.log(logging.FAILURE, msg, *args, **kwargs)


class AssertAdapter(logging.LoggerAdapter):
    """
    Wrap all messages with "assert: " and make the message yellow.
    """

    def process(self, msg, kwargs):
        return f"{Fore.YELLOW}assert: {msg}{Style.RESET_ALL}", kwargs

    @freeze_logging
    def verbose(self, msg, *args, **kwargs):
        self.log(logging.VERBOSE, msg, *args, **kwargs)

    @freeze_logging
    def notice(self, msg, *args, **kwargs):
        self.log(logging.NOTICE, msg, *args, **kwargs)

    @freeze_logging
    def success(self, msg, *args, **kwargs):
        self.log(logging.SUCCESS, msg, *args, **kwargs)

    @freeze_logging
    def spam(self, msg, *args, **kwargs):
        self.log(logging.SPAM, msg, *args, **kwargs)

    @freeze_logging
    def failure(self, msg, *args, **kwargs):
        self.log(logging.FAILURE, msg, *args, **kwargs)


class AuditorAdapter(logging.LoggerAdapter):
    """
    Wrap all messages with "auditor: " and make the message magenta.
    """

    def process(self, msg, kwargs):
        return f"{Fore.MAGENTA}auditor: {msg}{Style.RESET_ALL}", kwargs

    @freeze_logging
    def verbose(self, msg, *args, **kwargs):
        self.log(logging.VERBOSE, msg, *args, **kwargs)

    @freeze_logging
    def notice(self, msg, *args, **kwargs):
        self.log(logging.NOTICE, msg, *args, **kwargs)

    @freeze_logging
    def success(self, msg, *args, **kwargs):
        self.log(logging.SUCCESS, msg, *args, **kwargs)

    @freeze_logging
    def spam(self, msg, *args, **kwargs):
        self.log(logging.SPAM, msg, *args, **kwargs)

    @freeze_logging
    def failure(self, msg, *args, **kwargs):
        self.log(logging.FAILURE, msg, *args, **kwargs)


class LocalAdapter(logging.LoggerAdapter):
    """
    Wrap all messages with "local: " and make the message blue.
    """

    def process(self, msg, kwargs):
        return f"{Fore.BLUE}local: {msg}{Style.RESET_ALL}", kwargs

    @freeze_logging
    def verbose(self, msg, *args, **kwargs):
        self.log(logging.VERBOSE, msg, *args, **kwargs)

    @freeze_logging
    def notice(self, msg, *args, **kwargs):
        self.log(logging.NOTICE, msg, *args, **kwargs)

    @freeze_logging
    def success(self, msg, *args, **kwargs):
        self.log(logging.SUCCESS, msg, *args, **kwargs)

    @freeze_logging
    def spam(self, msg, *args, **kwargs):
        self.log(logging.SPAM, msg, *args, **kwargs)

    @freeze_logging
    def failure(self, msg, *args, **kwargs):
        self.log(logging.FAILURE, msg, *args, **kwargs)
