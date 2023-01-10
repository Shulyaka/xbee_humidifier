from json import loads as json_loads, dumps as json_dumps
from xbee import transmit, receive_callback
import logging


class Commands:
    _tosr0x_temp_binds = {}
    _tosr0x_relay_binds = {}
    _humidifier_available_binds = {}
    _pump_binds = {}

    def __init__(
        self,
        tosr_switch,
        tosr_temp,
        humidifier,
        humidifier_sensor,
        humidifier_available,
        humidifier_switch,
        pump,
        pump_block,
    ):
        self._tosr_switch = tosr_switch
        self._tosr_temp = tosr_temp
        self._humidifier = humidifier
        self._humidifier_sensor = humidifier_sensor
        self._humidifier_available = humidifier_available
        self._humidifier_switch = humidifier_switch
        self._pump = pump
        self._pump_block = pump_block

    def cmd_help(self, sender_eui64):
        return [cmd[4:] for cmd in dir(Commands) if cmd.startswith("cmd_")]

    def cmd_test(self, sender_eui64, *args, **kwargs):
        return "passed, args: " + str(args) + ", kwargs: " + str(kwargs)

    def cmd_logger_set_target(self, sender_eui64, target=None, name=None):
        if name:
            logging.getLogger(name).set_target(
                sender_eui64 if target is None else target
            )
        else:
            logging.getLogger("__main__").set_default_target(
                sender_eui64 if target is None else target
            )

    def cmd_logger_set_level(self, sender_eui64, level, name=None):
        if name:
            logging.getLogger(name).set_level(level)
        else:
            logging.getLogger("__main__").set_default_level(level)

    def cmd_humidifier_get_state(self, sender_eui64, number):
        return {
            "name": self._humidifier[number].name,
            "available": self._humidifier[number].available,
            "is_on": self._humidifier[number].is_on,
            "working": self._tosr_switch.state,
            "device_class": self._humidifier[number].device_class,
            "capability_attributes": self._humidifier[number].capability_attributes,
            "state_attributes": self._humidifier[number].state_attributes,
            "extra_state_attributes": self._humidifier[number].extra_state_attributes,
        }

    def cmd_humidifier_turn_on(self, sender_eui64, number):
        self._humidifier[number].turn_on()

    def cmd_humidifier_turn_off(self, sender_eui64, number):
        self._humidifier[number].turn_off()

    def cmd_humidifier_set_humidity(self, sender_eui64, number, value):
        self._humidifier[number].set_humidity(value)

    def cmd_humidifier_set_mode(self, sender_eui64, number, mode):
        self._humidifier[number].set_mode(mode)

    def cmd_humidifier_set_current_humidity(self, sender_eui64, number, value):
        self._humidifier_sensor[number].state = value

    def cmd_bind_humidifier_available(self, sender_eui64, number):
        if (
            number not in self._humidifier_available_binds
            and number in self._humidifier_available
        ):
            self._humidifier_available_binds[number] = {}
        if sender_eui64 not in self._humidifier_available_binds[number]:
            self._humidifier_available_binds[number][
                sender_eui64
            ] = self._humidifier_available[number].subscribe(
                lambda x: transmit(
                    sender_eui64,
                    json_dumps({"name": self._humidifier[number].name, "available": x}),
                )
            )

    def cmd_unbind_humidifier_available(self, sender_eui64, number):
        if sender_eui64 is None:
            if number in self._humidifier_available_binds:
                for unsubscribe in self._humidifier_available_binds[number]:
                    unsubscribe()
                self._humidifier_available_binds[number] = {}
        elif (
            number in self._humidifier_available_binds
            and sender_eui64 in self._humidifier_available_binds[number]
        ):
            self._humidifier_available_binds[number].pop(sender_eui64)()

    def cmd_bind_humidifier_working(self, sender_eui64, number):
        if (
            number not in self._humidifier_switch_binds
            and number in self._humidifier_switch
        ):
            self._humidifier_switch_binds[number] = {}
        if sender_eui64 not in self._humidifier_switch_binds[number]:
            self._humidifier_switch_binds[number][
                sender_eui64
            ] = self._humidifier_switch[number].subscribe(
                lambda x: transmit(
                    sender_eui64,
                    json_dumps({"name": self._humidifier[number].name, "working": x}),
                )
            )

    def cmd_unbind_humidifier_working(self, sender_eui64, number):
        if sender_eui64 is None:
            if number in self._humidifier_switch_binds:
                for unsubscribe in self._humidifier_switch_binds[number]:
                    unsubscribe()
                self._humidifier_switch_binds[number] = {}
        elif (
            number in self._humidifier_switch_binds
            and sender_eui64 in self._humidifier_switch_binds[number]
        ):
            self._humidifier_switch_binds[number].pop(sender_eui64)()

    def cmd_humidifier_override_switch(self, sender_eui64, number, value):
        self._humidifier_switch[number].state = value

    def cmd_pump_turn_on(self, sender_eui64):
        self._pump.state = True

    def cmd_pump_turn_off(self, sender_eui64):
        self._pump.state = False

    def cmd_bind_pump(self, sender_eui64):
        if sender_eui64 not in self._pump_binds:
            self._pump_binds[sender_eui64] = self._pump.subscribe(
                lambda x: transmit(sender_eui64, json_dumps({"pump": x}))
            )

    def cmd_unbind_pump(self, sender_eui64):
        if sender_eui64 is None:
            for unsubscribe in self._pump_binds.values():
                unsubscribe()
            self._pump_binds = {}
        elif sender_eui64 in self._pump_binds:
            self._pump_binds.pop(sender_eui64)()

    def cmd_get_pump_block(self, sender_eui64):
        return self._pump_block.state

    def cmd_set_pump_block(self, sender_eui64, value):
        self._pump_block.state = value

    def cmd_tosr0x_get_temp(self, sender_eui64):
        return self._tosr_temp.state

    def cmd_tosr0x_get_relay_state(self, sender_eui64, switch_number):
        return self._tosr_switch[switch_number].state

    def cmd_tosr0x_set_relay_state(self, sender_eui64, switch_number, state):
        self._tosr_switch[switch_number].state = state

    def cmd_bind_tosr0x_relay(self, sender_eui64, switch_number):
        if (
            switch_number not in self._tosr0x_relay_binds
            and switch_number in self._tosr_switch
        ):
            self._tosr0x_relay_binds[switch_number] = {}
        if sender_eui64 not in self._tosr0x_relay_binds[switch_number]:
            self._tosr0x_relay_binds[switch_number][sender_eui64] = self._tosr_switch[
                switch_number
            ].subscribe(
                lambda x: transmit(
                    sender_eui64, json_dumps({"tosr0x_relay_" + str(switch_number): x})
                )
            )

    def cmd_unbind_tosr0x_relay(self, sender_eui64, switch_number):
        if sender_eui64 is None:
            if switch_number in self._tosr0x_relay_binds:
                for unsubscribe in self._tosr0x_relay_binds[switch_number]:
                    unsubscribe()
                self._tosr0x_relay_binds[switch_number] = {}
        elif (
            switch_number in self._tosr0x_relay_binds
            and sender_eui64 in self._tosr0x_relay_binds[switch_number]
        ):
            self._tosr0x_relay_binds[switch_number].pop(sender_eui64)()

    def cmd_bind_tosr0x_temp(self, sender_eui64):
        if sender_eui64 not in self._tosr0x_temp_binds:
            self._tosr0x_temp_binds[sender_eui64] = self._tosr_temp.subscribe(
                lambda x: transmit(sender_eui64, json_dumps({"tosr0x_temp": x}))
            )

    def cmd_unbind_tosr0x_temp(self, sender_eui64):
        if sender_eui64 is None:
            for unsubscribe in self._tosr0x_temp_binds.values():
                unsubscribe()
            self._tosr0x_temp_binds = {}
        elif sender_eui64 in self._tosr0x_temp_binds:
            self._tosr0x_temp_binds.pop(sender_eui64)()

    def cmd_bind(self, sender_eui64):
        self.cmd_bind_tosr0x_temp(sender_eui64)
        self.cmd_bind_pump(sender_eui64)
        for x in range(5):
            self.cmd_bind_tosr0x_relay(sender_eui64, x)
        for x in range(3):
            self.cmd_bind_humidifier_available(sender_eui64, x)
            self.cmd_bind_humidifier_working(sender_eui64, x)

    def cmd_unbind(self, sender_eui64=None):
        self.cmd_unbind_tosr0x_temp(sender_eui64)
        self.cmd_unbind_pump(sender_eui64)
        for x in range(5):
            self.cmd_unbind_tosr0x_relay(sender_eui64, x)
        for x in range(3):
            self.cmd_unbind_humidifier_available(sender_eui64, x)
            self.cmd_unbind_humidifier_working(sender_eui64, x)


_commands = None


def register(*args, **kwargs):
    _commands = Commands(*args, **kwargs)

    def rx_callback(x):
        # Example: {'broadcast': False, 'dest_ep': 232, 'sender_eui64': b'\x00\x13\xa2\x00A\xa0n`', 'payload': b'{"command": "test"}', 'sender_nwk': 0, 'source_ep': 232, 'profile': 49413, 'cluster': 17}
        try:
            if x["payload"] == "":
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
                        **args, sender_eui64=x["sender_eui64"]
                    )
                elif isinstance(args, list):
                    response = getattr(_commands, "cmd_" + cmd)(
                        *args, sender_eui64=x["sender_eui64"]
                    )
                else:
                    response = getattr(_commands, "cmd_" + cmd)(
                        args, sender_eui64=x["sender_eui64"]
                    )
                if response is None:
                    response = "OK"
                response = {"cmd_" + cmd + "_resp": response}
            else:
                raise AttributeError("No such command")
        except Exception as e:
            response = {"errors": e}

        try:
            transmit(x["sender_eui64"], json_dumps(response))
        except Exception as e:
            _LOGGER.error("Exception: %s", e)

    receive_callback(rx_callback)


def unregister():
    if _commands:
        _commands.cmd_unbind()
    receive_callback(None)
    _commands = None
