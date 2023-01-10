"""Micro python ulogging implementation for xbee sending logs remotely."""

from micropython import const
from xbee import ADDR_COORDINATOR, transmit

DEBUG = const(5)
INFO = const(4)
WARNING = const(3)
ERROR = const(2)
CRITICAL = const(1)

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

        def set_target(self, target=ADDR_COORDINATOR):
            """Override default target device eui64."""
            self._target = target

        def set_default_target(self, target=ADDR_COORDINATOR):
            """Update default target device eui64."""
            Logger._target = target

        def set_level(self, level):
            """Override default logging level."""
            self._level = level

        def set_default_level(self, level):
            """Update default logging level."""
            Logger._level = level

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
            if self._level >= DEBUG:
                self._log("DEBUG: " + str(msg), *args, **kwargs)

        def info(self, msg, *args, **kwargs):
            """Write info logs."""
            if self._level >= INFO:
                self._log("INFO: " + str(msg), *args, **kwargs)

        def warning(self, msg, *args, **kwargs):
            """Write warning logs."""
            if self._level >= WARNING:
                self._log("WARNING: " + str(msg), *args, **kwargs)

        def error(self, msg, *args, **kwargs):
            """Write error logs."""
            if self._level >= ERROR:
                self._log("ERROR: " + str(msg), *args, **kwargs)

        def critical(self, msg, *args, **kwargs):
            """Write critical logs."""
            if self._level >= CRITICAL:
                self._log("CRITICAL: " + str(msg), *args, **kwargs)

    _loggers[name] = Logger(name=name)
    return _loggers[name]
