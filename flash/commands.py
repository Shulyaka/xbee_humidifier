"""Module defines remote commands."""

from json import dumps as json_dumps, loads as json_loads

from lib import logging
from lib.mainloop import main_loop
from machine import soft_reset
from xbee import receive, transmit

_LOGGER = logging.getLogger(__name__)


class Commands:
    """Define application remote commands."""

    def __init__(
        self,
        valve,
        pump_temp,
        humidifier,
        humidifier_sensor,
        humidifier_available,
        humidifier_zone,
        pump,
        pump_block,
    ):
        """Init the module."""
        self._valve = valve
        self._pump_temp = pump_temp
        self._humidifier = humidifier
        self._humidifier_sensor = humidifier_sensor
        self._humidifier_available = humidifier_available
        self._humidifier_zone = humidifier_zone
        self._pump = pump
        self._pump_block = pump_block

        self._pump_temp_binds = {}
        self._valve_binds = {}
        self._humidifier_binds = {}
        self._pump_binds = {}

        self._unschedule = main_loop.schedule_task(lambda: self.update(), period=500)

    def __del__(self):
        """Cancel callbacks."""
        self._unschedule()
        self.cmd_unbind()

    def update(self):
        """Receive commands."""
        x = receive()
        if x is None:
            return

        # Example: {'broadcast': False, 'dest_ep': 232, 'sender_eui64': b'\x00\x13\xa2\x00A\xa0n`', 'payload': b'{"command": "test"}', 'sender_nwk': 0, 'source_ep': 232, 'profile': 49413, 'cluster': 17}
        try:
            d = x["payload"]
            if d is None or d in (b"", b"\n", b"\r"):
                return
            d = json_loads(d)
            cmd = d["command"]
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
            response = {"err": type(e).__name__ + ": " + str(e)}

        try:
            transmit(x["sender_eui64"], json_dumps(response))
        except Exception as e:
            _LOGGER.error("Exception: %s: %s", type(e).__name__, e)

    def cmd_help(self, sender_eui64):
        """Return the list of available commands."""
        return [cmd[4:] for cmd in dir(Commands) if cmd.startswith("cmd_")]

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

    def cmd_hum(
        self,
        sender_eui64,
        number,
        is_on=None,
        working=None,
        mode=None,
        hum=None,
        cur_hum=None,
    ):
        """Get or set the humidifier state."""
        if (
            is_on is None
            and working is None
            and mode is None
            and hum is None
            and cur_hum is None
        ):
            return {
                "number": number,
                "available": self._humidifier_available[number].state,
                "is_on": self._humidifier[number].state,
                "working": self._humidifier_zone[number].state,
                "cap_attr": self._humidifier[number].capability_attributes,
                "state_attr": self._humidifier[number].state_attributes,
                "extra_state_attr": self._humidifier[number].extra_state_attributes,
            }

        if is_on is not None:
            self._humidifier[number].state = is_on
        if working is not None:
            self._humidifier_zone[number].state = working
        if mode is not None:
            self._humidifier[number].set_mode(mode)
        if hum is not None:
            self._humidifier[number].set_humidity(hum)
        if cur_hum is not None:
            self._humidifier_sensor[number].state = cur_hum

    def cmd_hum_bind(self, sender_eui64, number, target=None):
        """Subscribe to humidifier updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64

        if number not in self._humidifier_binds and number in self._humidifier:
            self._humidifier_binds[number] = {}
        if target not in self._humidifier_binds[number]:
            self._humidifier_binds[number][target] = (
                self._humidifier_available[number].subscribe(
                    lambda x: transmit(
                        target,
                        json_dumps({"number": number, "available": x}),
                    )
                ),
                self._humidifier_zone[number].subscribe(
                    lambda x: transmit(
                        target,
                        json_dumps({"number": number, "working": x}),
                    )
                ),
            )

    def cmd_hum_unbind(self, sender_eui64, number, target=None):
        """Unsubscribe to humidifier updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target is None:
            if number in self._humidifier_binds:
                for unsubscribe_available, unsubscribe_zone in self._humidifier_binds[
                    number
                ].values():
                    unsubscribe_available()
                    unsubscribe_zone()
                self._humidifier_binds[number] = {}
        elif (
            number in self._humidifier_binds
            and target in self._humidifier_binds[number]
        ):
            unsubscribe_available, unsubscribe_zone = self._humidifier_binds[
                number
            ].pop(target)
            unsubscribe_available()
            unsubscribe_zone()

    def cmd_pump(self, sender_eui64, state=None):
        """Get or set the pump state."""
        if state is None:
            return self._pump.state
        else:
            self._pump.state = state

    def cmd_pump_bind(self, sender_eui64, target=None):
        """Subscribe to humidifier pump updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target not in self._pump_binds:
            self._pump_binds[target] = self._pump.subscribe(
                lambda x: transmit(target, json_dumps({"pump": x}))
            )

    def cmd_pump_unbind(self, sender_eui64, target=None):
        """Unsubscribe to humidifier pump updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target is None:
            for unsubscribe in self._pump_binds.values():
                unsubscribe()
            self._pump_binds = {}
        elif target in self._pump_binds:
            self._pump_binds.pop(target)()

    def cmd_pump_block(self, sender_eui64, state=None):
        """Get or set the status of pump block."""
        if state is None:
            return self._pump_block.state
        else:
            self._pump_block.state = state

    def cmd_pump_temp(self, sender_eui64):
        """Get current pump temperature."""
        return self._pump_temp.state

    def cmd_valve(self, sender_eui64, number, state=None):
        """Get or set the current valve status."""
        if state is None:
            return self._valve[number].state
        else:
            self._valve[number].state = state

    def cmd_valve_bind(self, sender_eui64, number, target=None):
        """Subscribe to valve updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if number not in self._valve_binds and number in self._valve:
            self._valve_binds[number] = {}
        if target not in self._valve_binds[number]:
            self._valve_binds[number][target] = self._valve[number].subscribe(
                lambda x: transmit(target, json_dumps({"valve_" + str(number): x}))
            )

    def cmd_valve_unbind(self, sender_eui64, number, target=None):
        """Unsubscribe to valve updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target is None:
            if number in self._valve_binds:
                for unsubscribe in self._valve_binds[number].values():
                    unsubscribe()
                self._valve_binds[number] = {}
        elif number in self._valve_binds and target in self._valve_binds[number]:
            self._valve_binds[number].pop(target)()

    def cmd_pump_temp_bind(self, sender_eui64, target=None):
        """Subscribe to pump temperature updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target not in self._pump_temp_binds:
            self._pump_temp_binds[target] = self._pump_temp.subscribe(
                lambda x: transmit(target, json_dumps({"pump_temp": x}))
            )

    def cmd_pump_temp_unbind(self, sender_eui64, target=None):
        """Unsubscribe to pump temperature updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target is None:
            for unsubscribe in self._pump_temp_binds.values():
                unsubscribe()
            self._pump_temp_binds = {}
        elif target in self._pump_temp_binds:
            self._pump_temp_binds.pop(target)()

    def cmd_bind(self, sender_eui64, target=None):
        """Subscribe to all updates."""
        self.cmd_pump_temp_bind(sender_eui64, target)
        self.cmd_pump_bind(sender_eui64, target)
        for x in range(4):
            self.cmd_valve_bind(sender_eui64, x, target)
        for x in range(3):
            self.cmd_hum_bind(sender_eui64, x, target)

    def cmd_unbind(self, sender_eui64=None, target=None):
        """Unsubscribe to all updates."""
        self.cmd_pump_temp_unbind(sender_eui64, target)
        self.cmd_pump_unbind(sender_eui64, target)
        for x in range(4):
            self.cmd_valve_unbind(sender_eui64, x, target)
        for x in range(3):
            self.cmd_hum_unbind(sender_eui64, x, target)

    def cmd_soft_reset(self, sender_eui64=None):
        """Schedule soft reset."""
        main_loop.schedule_task(soft_reset)
