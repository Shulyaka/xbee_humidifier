"""Micropython logging implementation for xbee sending logs remotely."""

from micropython import const
from xbee import ADDR_COORDINATOR, transmit

DEBUG = const(10)
INFO = const(20)
WARNING = const(30)
ERROR = const(40)
CRITICAL = const(50)

_loggers = {}


def getLogger(name):
    """Create or reuse logger for the specified name."""

    class Logger:
        """XBee remote logger."""

        _target = ADDR_COORDINATOR
        _level = DEBUG

        def __init__(self, name=None):
            """Init the class."""
            self._name = name

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
            if self._name:
                msg = self._name + ": " + msg
            if args:
                msg = msg % args
            return msg + "\n"

        def _log(self, msg, *args, **kwargs):
            try:
                transmit(self._target, self.makeRecord(msg, *args, **kwargs))
            except Exception:
                pass

        def debug(self, msg, *args, **kwargs):
            """Write debug logs."""
            if self._level <= DEBUG:
                self._log("DEBUG: " + str(msg), *args, **kwargs)

        def info(self, msg, *args, **kwargs):
            """Write info logs."""
            if self._level <= INFO:
                self._log("INFO: " + str(msg), *args, **kwargs)

        def warning(self, msg, *args, **kwargs):
            """Write warning logs."""
            if self._level <= WARNING:
                self._log("WARNING: " + str(msg), *args, **kwargs)

        def error(self, msg, *args, **kwargs):
            """Write error logs."""
            if self._level <= ERROR:
                self._log("ERROR: " + str(msg), *args, **kwargs)

        def critical(self, msg, *args, **kwargs):
            """Write critical logs."""
            if self._level <= CRITICAL:
                self._log("CRITICAL: " + str(msg), *args, **kwargs)

    if name not in _loggers:
        _loggers[name] = Logger(name=name)

    return _loggers[name]
