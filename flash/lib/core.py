"""Implementation of Sensor and Switch classes with event subscription support."""

from binascii import hexlify
from gc import collect
from json import dumps as json_dumps, loads as json_loads
from time import ticks_diff, ticks_ms

from lib import logging
from lib.mainloop import main_loop
from machine import reset_cause, soft_reset, unique_id
from xbee import ADDR_COORDINATOR, atcmd, receive, transmit

_LOGGER = logging.getLogger(__name__)


class Sensor:
    """Base class."""

    _type = None
    _cache = False
    _readonly = False
    _period = None
    _lowpass = None

    def __init__(self, value=None, period=None, lowpass=None):
        """Init the class."""
        self._triggers = []
        self._state = None
        self._last_callback_value = None
        self._last_callback_time = None
        if lowpass is not None and self._type is not bool:
            self._lowpass = lowpass if lowpass != 0 else None
        if period is not None:
            self._period = period if period != 0 else None
        try:
            if not self._readonly and (
                (self._type is None and value is not None)
                or (self._type is not None and self._type(value) is not None)
            ):
                self.state = value
        except TypeError:
            self.state = self._type()

        self.update()

        if self._period is not None:
            self._updates = main_loop.schedule_task(
                lambda: self.update(auto=True),
                next_run=self._period,
                period=self._period,
            )
        else:
            self._updates = None

    def __del__(self):
        """Cancel callbacks."""
        main_loop.remove_task(self._updates)

    def _run_triggers(self, value):
        """Call all defined callbacks one by one synchronically."""
        self._last_callback_value = value
        self._last_callback_time = ticks_ms()
        for callback in self._triggers:
            try:
                collect()
                callback(value)
                collect()
            except Exception as e:
                _LOGGER.error("callback error for {}".format(callback))
                _LOGGER.error("{}: {}".format(type(e).__name__, e))

    def subscribe(self, callback):
        """Add new callback."""
        collect()
        self._triggers.append(callback)
        collect()
        return callback

    def unsubscribe(self, callback):
        """Remove callback."""
        self._triggers.remove(callback)
        collect()

    @property
    def state(self):
        """Get cached state."""
        if self._cache:
            self.update(auto=True)
        return self._state

    @state.setter
    def state(self, value):
        """Set new state."""
        if self._readonly:
            return
        if self._type is not None:
            value = self._type(value)
        self._set(value)
        if value != self._state or self._state is None:
            self._state = value
            self._run_triggers(value)

    def update(self, auto=False):
        """Get updated state."""
        value = self._get()
        if self._type is not None:
            value = self._type(value)
        self._state = value
        if (
            self._last_callback_value is None
            or not auto
            or (
                self._lowpass is not None
                and abs(self._last_callback_value - self._state)
                * ticks_diff(ticks_ms(), self._last_callback_time)
                >= self._lowpass
            )
            or (self._lowpass is None and self._last_callback_value != self._state)
        ):
            self._run_triggers(self._state)

    def _get(self):
        """Read the value."""
        return self._state

    def _set(self, value):
        """Write the value."""


class Switch(Sensor):
    """Digital entity."""

    _type = bool


class Commands:
    """Define application remote commands."""

    def __init__(self):
        """Init the module."""
        self._updates = main_loop.schedule_task(lambda: self.update(), period=500)
        self._last_upd = ticks_ms()
        self._uptime = 0
        self._uptime_cb = main_loop.schedule_task(
            lambda: self._uptime_upd(), period=30000
        )

    def __del__(self):
        """Cancel callbacks."""
        main_loop.remove_task(self._updates)
        if self._uptime_cb is not None:
            main_loop.remove_task(self._uptime_cb)

    def update(self):
        """Receive commands."""
        x = receive()
        while x is not None:
            # Example: {
            #    "broadcast": False,
            #    "dest_ep": 232,
            #    "sender_eui64": b"\x00\x13\xa2\x00A\xa0n`",
            #    "payload": b'{"command": "test"}',
            #    "sender_nwk": 0,
            #    "source_ep": 232,
            #    "profile": 49413,
            #    "cluster": 17,
            # }
            try:
                cmd = None
                d = json_loads(x["payload"])
                cmd = d["cmd"]
                args = d.get("args")
                sender_eui64 = x["sender_eui64"]
                x = None
                d = None
                collect()
                method = "cmd_{}".format(cmd)
                if hasattr(self, method):
                    method = getattr(self, method)
                    if args is None:
                        response = method(sender_eui64=sender_eui64)
                    elif isinstance(args, dict):
                        response = method(sender_eui64=sender_eui64, **args)
                    elif (
                        isinstance(args, list)
                        and len(args) == 2
                        and isinstance(args[0], list)
                        and isinstance(args[1], dict)
                    ):
                        response = method(sender_eui64, *args[0], **args[1])
                    elif isinstance(args, list):
                        response = method(sender_eui64, *args)
                    else:
                        response = method(sender_eui64, args)
                    method = None
                    args = None
                    collect()
                    response = {"{}_resp".format(cmd): response}
                else:
                    raise AttributeError("No such command")
            except Exception as e:
                if cmd is not None:
                    response = {
                        "{}_resp".format(cmd): {
                            "err": "{}: {}".format(type(e).__name__, e)
                        }
                    }
                else:
                    raise ValueError("invalid json")

            self._transmit(sender_eui64, json_dumps(response))
            response = None
            sender_eui64 = None
            cmd = None
            collect()

            x = receive()

    def _transmit(self, eui64, data, limit=3):
        """Retries sending data on full transfer buffer."""
        try:
            transmit(eui64, data)
        except Exception as e:
            _LOGGER.error("Exception on transmit: {}: {}".format(type(e).__name__, e))
            if isinstance(e, OSError) and "EAGAIN" in str(e) and limit > 1:
                main_loop.schedule_task(
                    (
                        lambda eui64, data, limit: lambda: self._transmit(
                            eui64, data, limit
                        )
                    )(eui64, data, limit - 1),
                    next_run=50,
                )

    def _uptime_upd(self, auto=True):
        """Set uptime notification."""
        now = ticks_ms()
        self._uptime += ticks_diff(now, self._last_upd)
        self._last_upd = now
        if auto:
            self._transmit(
                ADDR_COORDINATOR, json_dumps({"uptime": -self._uptime / 1000})
            )

    def cmd_uptime(self, sender_eui64, uptime=None):
        """Get or set uptime."""
        if self._uptime_cb is not None:
            self._uptime_upd(auto=False)
        if uptime is None:
            if self._uptime_cb is None:
                return self._uptime
            return -self._uptime / 1000
        self._uptime = uptime
        main_loop.remove_task(self._uptime_cb)
        self._uptime_cb = None
        return "OK"

    def cmd_help(self, sender_eui64=None):
        """Return the list of available commands."""
        return [cmd[4:] for cmd in dir(self) if cmd.startswith("cmd_")]

    def cmd_test(self, sender_eui64, *args, **kwargs):
        """Echo arguments."""
        return "args: {}, kwargs: {}".format(args, kwargs)

    def cmd_logger(self, sender_eui64=None, level=None, target=None):
        """Set logging level and target."""
        if level is not None:
            logging.getLogger().setLevel(level)
        if target is not None or (level is None and sender_eui64 is not None):
            target = (
                bytes(target, encoding="utf-8") if target is not None else sender_eui64
            )
            logging.getLogger().setTarget(target)
        return "OK"

    def cmd_soft_reset(self, sender_eui64=None):
        """Schedule soft reset."""
        main_loop.schedule_task(soft_reset)
        return "OK"

    def cmd_reset_cause(self, sender_eui64=None):
        """Return the reset cause."""
        return reset_cause()

    def cmd_unique_id(self, sender_eui64=None):
        """Return the unique identifier for the processor."""
        return hexlify(unique_id()).decode()

    def cmd_atcmd(self, sender_eui64, *args, **kwargs):
        """Execute AT command and returns the result."""
        return atcmd(*args, **kwargs)
