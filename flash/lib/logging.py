"""Micropython logging implementation for xbee sending logs remotely."""

from micropython import const
from xbee import ADDR_COORDINATOR, transmit

DEBUG = const(10)
INFO = const(20)
WARNING = const(30)
ERROR = const(40)
CRITICAL = const(50)


class Logger:
    """XBee remote logger."""

    def __init__(self, name=None):
        """Init the class."""
        self._target = ADDR_COORDINATOR
        self._level = DEBUG

    def setTarget(self, target=ADDR_COORDINATOR):
        """Update target device eui64."""
        self._target = target

    def setLevel(self, level):
        """Update logging level."""
        self._level = level

    def getEffectiveLevel(self):
        """Get logging level."""
        return self._level

    def makeRecord(self, msg, *args, **kwargs):
        """Format the record."""
        if args:
            msg = msg % args
        return msg + "\n"

    def _log(self, msg, *args, **kwargs):
        try:
            transmit(self._target, self.makeRecord(msg, *args, **kwargs))
        except Exception:
            pass

    def log(self, level, msg, *args, **kwargs):
        """Write logs."""
        if self._level <= level:
            self._log(str(level) + ": " + str(msg), *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """Write debug logs."""
        self.log(DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Write info logs."""
        self.log(INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Write warning logs."""
        self.log(WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Write error logs."""
        self.log(ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Write critical logs."""
        self.log(CRITICAL, msg, *args, **kwargs)


logger = Logger()


def getLogger(name=None):
    """Compatibility function to get the logger."""

    return logger
