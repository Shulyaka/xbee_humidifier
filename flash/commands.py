"""Module defines remote commands."""

from json import dumps as json_dumps, loads as json_loads

from lib import logging
from xbee import receive_callback, transmit

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
        self._humidifier_available_binds = {}
        self._humidifier_zone_binds = {}
        self._pump_binds = {}

    def __del__(self):
        """Cancel callbacks."""
        self.cmd_unbind()

    def cmd_help(self, sender_eui64):
        """Return the list of available commands."""
        return [cmd[4:] for cmd in dir(Commands) if cmd.startswith("cmd_")]

    def cmd_test(self, sender_eui64, *args, **kwargs):
        """Echo arguments."""
        return "args: " + str(args) + ", kwargs: " + str(kwargs)

    def cmd_logger_set_target(self, sender_eui64, target=None):
        """Set logger target."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        logging.getLogger().setTarget(target)

    def cmd_logger_set_level(self, sender_eui64, level):
        """Set logging level."""
        logging.getLogger().setLevel(level)

    def cmd_humidifier_get_state(self, sender_eui64, number):
        """Get humidifier state."""
        return {
            "number": number,
            "available": self._humidifier_available[number].state,
            "is_on": self._humidifier[number].state,
            "working": self._humidifier_zone[number].state,
            "cap_attr": self._humidifier[number].capability_attributes,
            "state_attr": self._humidifier[number].state_attributes,
            "extra_state_attr": self._humidifier[number].extra_state_attributes,
        }

    def cmd_humidifier_set_state(self, sender_eui64, number, state):
        """Turn humidifier on or off."""
        self._humidifier[number].state = state

    def cmd_humidifier_set_humidity(self, sender_eui64, number, value):
        """Set target humidity."""
        self._humidifier[number].set_humidity(value)

    def cmd_humidifier_set_mode(self, sender_eui64, number, mode):
        """Set humidifier mode."""
        self._humidifier[number].set_mode(mode)

    def cmd_humidifier_set_current_humidity(self, sender_eui64, number, value):
        """Update current humidity."""
        self._humidifier_sensor[number].state = value

    def cmd_bind_humidifier_available(self, sender_eui64, number, target=None):
        """Subscribe to humidifier availability updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if (
            number not in self._humidifier_available_binds
            and number in self._humidifier_available
        ):
            self._humidifier_available_binds[number] = {}
        if target not in self._humidifier_available_binds[number]:
            self._humidifier_available_binds[number][
                target
            ] = self._humidifier_available[number].subscribe(
                lambda x: transmit(
                    target,
                    json_dumps({"number": number, "available": x}),
                )
            )

    def cmd_unbind_humidifier_available(self, sender_eui64, number, target=None):
        """Unsubscribe to humidifier availability updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target is None:
            if number in self._humidifier_available_binds:
                for unsubscribe in self._humidifier_available_binds[number]:
                    unsubscribe()
                self._humidifier_available_binds[number] = {}
        elif (
            number in self._humidifier_available_binds
            and target in self._humidifier_available_binds[number]
        ):
            self._humidifier_available_binds[number].pop(target)()

    def cmd_bind_humidifier_working(self, sender_eui64, number, target=None):
        """Subscribe to humidifier zone updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if (
            number not in self._humidifier_zone_binds
            and number in self._humidifier_zone
        ):
            self._humidifier_zone_binds[number] = {}
        if target not in self._humidifier_zone_binds[number]:
            self._humidifier_zone_binds[number][target] = self._humidifier_zone[
                number
            ].subscribe(
                lambda x: transmit(
                    target,
                    json_dumps({"number": number, "working": x}),
                )
            )

    def cmd_unbind_humidifier_working(self, sender_eui64, number, target=None):
        """Unsubscribe to humidifier zone updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target is None:
            if number in self._humidifier_zone_binds:
                for unsubscribe in self._humidifier_zone_binds[number]:
                    unsubscribe()
                self._humidifier_zone_binds[number] = {}
        elif (
            number in self._humidifier_zone_binds
            and target in self._humidifier_zone_binds[number]
        ):
            self._humidifier_zone_binds[number].pop(target)()

    def cmd_humidifier_override_zone(self, sender_eui64, number, value):
        """Manually set humidifier zone state."""
        self._humidifier_zone[number].state = value

    def cmd_set_pump(self, sender_eui64, value):
        """Manually turn on or off the pump."""
        self._pump.state = value

    def cmd_bind_pump(self, sender_eui64, target=None):
        """Subscribe to humidifier pump updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target not in self._pump_binds:
            self._pump_binds[target] = self._pump.subscribe(
                lambda x: transmit(target, json_dumps({"pump": x}))
            )

    def cmd_unbind_pump(self, sender_eui64, target=None):
        """Unsubscribe to humidifier pump updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target is None:
            for unsubscribe in self._pump_binds.values():
                unsubscribe()
            self._pump_binds = {}
        elif target in self._pump_binds:
            self._pump_binds.pop(target)()

    def cmd_get_pump_block(self, sender_eui64):
        """Get status of pump block."""
        return self._pump_block.state

    def cmd_set_pump_block(self, sender_eui64, value):
        """Update state of pump block."""
        self._pump_block.state = value

    def cmd_get_pump_temp(self, sender_eui64):
        """Get current pump temperature."""
        return self._pump_temp.state

    def cmd_get_valve_state(self, sender_eui64, switch_number):
        """Get current valve status."""
        return self._valve[switch_number].state

    def cmd_set_valve_state(self, sender_eui64, switch_number, state):
        """Manually update valve status."""
        self._valve[switch_number].state = state

    def cmd_bind_valve(self, sender_eui64, switch_number, target=None):
        """Subscribe to valve updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if switch_number not in self._valve_binds and switch_number in self._valve:
            self._valve_binds[switch_number] = {}
        if target not in self._valve_binds[switch_number]:
            self._valve_binds[switch_number][target] = self._valve[
                switch_number
            ].subscribe(
                lambda x: transmit(
                    target, json_dumps({"valve_" + str(switch_number): x})
                )
            )

    def cmd_unbind_valve(self, sender_eui64, switch_number, target=None):
        """Unsubscribe to valve updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target is None:
            if switch_number in self._valve_binds:
                for unsubscribe in self._valve_binds[switch_number]:
                    unsubscribe()
                self._valve_binds[switch_number] = {}
        elif (
            switch_number in self._valve_binds
            and target in self._valve_binds[switch_number]
        ):
            self._valve_binds[switch_number].pop(target)()

    def cmd_bind_pump_temp(self, sender_eui64, target=None):
        """Subscribe to pump temperature updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64
        if target not in self._pump_temp_binds:
            self._pump_temp_binds[target] = self._pump_temp.subscribe(
                lambda x: transmit(target, json_dumps({"pump_temp": x}))
            )

    def cmd_unbind_pump_temp(self, sender_eui64, target=None):
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
        self.cmd_bind_pump_temp(sender_eui64, target)
        self.cmd_bind_pump(sender_eui64, target)
        for x in range(4):
            self.cmd_bind_valve(sender_eui64, x, target)
        for x in range(3):
            self.cmd_bind_humidifier_available(sender_eui64, x, target)
            self.cmd_bind_humidifier_working(sender_eui64, x, target)

    def cmd_unbind(self, sender_eui64=None, target=None):
        """Unsubscribe to all updates."""
        self.cmd_unbind_pump_temp(sender_eui64, target)
        self.cmd_unbind_pump(sender_eui64, target)
        for x in range(4):
            self.cmd_unbind_valve(sender_eui64, x, target)
        for x in range(3):
            self.cmd_unbind_humidifier_available(sender_eui64, x, target)
            self.cmd_unbind_humidifier_working(sender_eui64, x, target)


_commands = None


def register(*args, **kwargs):
    """Register command handler."""
    global _commands
    _commands = Commands(*args, **kwargs)

    def rx_callback(x):
        # Example: {'broadcast': False, 'dest_ep': 232, 'sender_eui64': b'\x00\x13\xa2\x00A\xa0n`', 'payload': b'{"command": "test"}', 'sender_nwk': 0, 'source_ep': 232, 'profile': 49413, 'cluster': 17}
        try:
            if x["payload"] is None:
                return
            d = json_loads(x["payload"])
            cmd = d["command"]
            args = d.get("args")
            if hasattr(_commands, "cmd_" + cmd):
                if args is None:
                    response = getattr(_commands, "cmd_" + cmd)(
                        sender_eui64=x["sender_eui64"]
                    )
                elif isinstance(args, dict):
                    response = getattr(_commands, "cmd_" + cmd)(
                        sender_eui64=x["sender_eui64"], **args
                    )
                elif isinstance(args, list):
                    response = getattr(_commands, "cmd_" + cmd)(
                        x["sender_eui64"], *args
                    )
                else:
                    response = getattr(_commands, "cmd_" + cmd)(x["sender_eui64"], args)
                if response is None:
                    response = "OK"
                response = {"cmd_" + cmd + "_resp": response}
            else:
                raise AttributeError("No such command")
        except Exception as e:
            response = {"error": type(e).__name__ + ": " + str(e)}

        try:
            transmit(x["sender_eui64"], json_dumps(response))
        except Exception as e:
            _LOGGER.error("Exception: %s: %s", type(e).__name__, e)

    receive_callback(rx_callback)


def unregister():
    """Unregister command handler."""
    global _commands
    if _commands:
        _commands.cmd_unbind()
    receive_callback(None)
    _commands = None
