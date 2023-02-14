"""Implementation of Entity classes with subscription support."""

from gc import collect
from json import dumps as json_dumps, loads as json_loads

from lib import logging
from lib.mainloop import main_loop
from machine import soft_reset
from xbee import receive, transmit

_LOGGER = logging.getLogger(__name__)


class Entity:
    """Base class."""

    def __init__(self):
        """Init the class."""
        self._triggers = []

    def _run_triggers(self, value):
        """Call all defined callbacks one by one synchronically."""
        for callback in self._triggers:
            try:
                callback(value)
                collect()
            except Exception as e:
                _LOGGER.error("callback error for %s", callback)
                _LOGGER.error(type(e).__name__ + ": " + str(e))
                raise

    def subscribe(self, callback):
        """Add new callback."""
        self._triggers.append(callback)
        return lambda: self._triggers.remove(callback)

    @property
    def state(self):
        """Get cached state."""
        pass

    @state.setter
    def state(self, value):
        """Set new state."""
        self._run_triggers(value)

    def update(self):
        """Get updated state."""
        pass


class VirtualSwitch(Entity):
    """Virtual digital entity."""

    _type = bool

    def __init__(self, value=None):
        """Init the class."""
        super().__init__()
        self.state = value

    @property
    def state(self):
        """Get cached state."""
        return self._state

    @state.setter
    def state(self, value):
        """Set new state."""
        self._state = self._type(value) if self._type is not None else value
        self._run_triggers(self._state)


class VirtualSensor(VirtualSwitch):
    """Virtual numeric entity."""

    _type = None


class Commands:
    """Define application remote commands."""

    def __init__(self):
        """Init the module."""
        self._unschedule = main_loop.schedule_task(lambda: self.update(), period=500)

    def __del__(self):
        """Cancel callbacks."""
        self._unschedule()

    def update(self):
        """Receive commands."""
        x = receive()
        while x is not None:
            # Example: {'broadcast': False, 'dest_ep': 232, 'sender_eui64': b'\x00\x13\xa2\x00A\xa0n`', 'payload': b'{"command": "test"}', 'sender_nwk': 0, 'source_ep': 232, 'profile': 49413, 'cluster': 17}
            try:
                cmd = None
                d = json_loads(x["payload"])
                cmd = d["cmd"]
                args = d.get("args")
                if hasattr(self, "cmd_" + cmd):
                    if args is None:
                        response = getattr(self, "cmd_" + cmd)(
                            sender_eui64=x["sender_eui64"]
                        )
                    elif isinstance(args, dict):
                        response = getattr(self, "cmd_" + cmd)(
                            sender_eui64=x["sender_eui64"], **args
                        )
                    elif (
                        isinstance(args, list)
                        and len(args) == 2
                        and isinstance(args[0], list)
                        and isinstance(args[1], dict)
                    ):
                        response = getattr(self, "cmd_" + cmd)(
                            x["sender_eui64"], *args[0], **args[1]
                        )
                    elif isinstance(args, list):
                        response = getattr(self, "cmd_" + cmd)(x["sender_eui64"], *args)
                    else:
                        response = getattr(self, "cmd_" + cmd)(x["sender_eui64"], args)
                    if response is None:
                        response = "OK"
                    response = {cmd + "_resp": response}
                else:
                    raise AttributeError("No such command")
            except Exception as e:
                if cmd is not None:
                    response = {
                        cmd + "_resp": {"err": type(e).__name__ + ": " + str(e)}
                    }
                else:
                    raise ValueError("invalid json")

            self._transmit(x["sender_eui64"], json_dumps(response))

            x = receive()

    def _transmit(self, eui64, data):
        """Retries sending data on insufficient buffers, packet already queued for target."""
        try:
            transmit(eui64, data)
        except Exception as e:
            _LOGGER.error("Exception on transmit: %s: %s", type(e).__name__, e)
            if isinstance(e, OSError) and "EAGAIN" in str(e):
                main_loop.schedule_task(
                    (lambda eui64, data: lambda: self._transmit(eui64, data))(
                        eui64, data
                    )
                )

    def cmd_help(self, sender_eui64):
        """Return the list of available commands."""
        return [cmd[4:] for cmd in dir(self) if cmd.startswith("cmd_")]

    def cmd_test(self, sender_eui64, *args, **kwargs):
        """Echo arguments."""
        return "args: " + str(args) + ", kwargs: " + str(kwargs)

    def cmd_logger(self, sender_eui64, level=None, target=None):
        """Set logging level and target."""
        if level is not None:
            logging.getLogger().setLevel(level)
        if target is not None or level is None:
            target = (
                bytes(target, encoding="utf-8") if target is not None else sender_eui64
            )
            logging.getLogger().setTarget(target)

    def cmd_soft_reset(self, sender_eui64=None):
        """Schedule soft reset."""
        main_loop.schedule_task(soft_reset)
