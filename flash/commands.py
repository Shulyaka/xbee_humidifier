"""Module defines remote commands."""

from json import dumps as json_dumps

from lib.core import Commands


class HumidifierCommands(Commands):
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
        super().__init__()
        self._valve = valve
        self._pump_temp = pump_temp
        self._humidifier = humidifier
        self._humidifier_sensor = humidifier_sensor
        self._humidifier_available = humidifier_available
        self._humidifier_zone = humidifier_zone
        self._pump = pump
        self._pump_block = pump_block

        self._binds = {"pump_temp": {}, "valve": {}, "hum": {}, "pump": {}}

    def __del__(self):
        """Cancel callbacks."""
        super().__del__()
        self.cmd_unbind()

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
                "cur_hum": self._humidifier_sensor[number].state,
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

    def cmd_pump(self, sender_eui64, state=None):
        """Get or set the pump state."""
        if state is None:
            return self._pump.state
        self._pump.state = state

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
        self._valve[number].state = state

    def cmd_bind(self, sender_eui64, target=None):
        """Subscribe to updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64

        if target not in self._binds["pump_temp"]:
            self._binds["pump_temp"][target] = self._pump_temp.subscribe(
                lambda x: self._transmit(target, json_dumps({"pump_temp": x}))
            )

        if target not in self._binds["pump"]:
            self._binds["pump"][target] = self._pump.subscribe(
                lambda x: self._transmit(target, json_dumps({"pump": x}))
            )

        for number in range(4):
            if number not in self._binds["valve"] and number in self._valve:
                self._binds["valve"][number] = {}
            if target not in self._binds["valve"][number]:
                self._binds["valve"][number][target] = self._valve[number].subscribe(
                    (
                        lambda number: lambda x: self._transmit(
                            target, json_dumps({"valve_" + str(number): x})
                        )
                    )(number)
                )

        for number in range(3):
            if number not in self._binds["hum"] and number in self._humidifier:
                self._binds["hum"][number] = {}
            if target not in self._binds["hum"][number]:
                self._binds["hum"][number][target] = (
                    self._humidifier_available[number].subscribe(
                        (
                            lambda number: lambda x: self._transmit(
                                target, json_dumps({"available_" + str(number): x})
                            )
                        )(number)
                    ),
                    self._humidifier_zone[number].subscribe(
                        (
                            lambda number: lambda x: self._transmit(
                                target, json_dumps({"working_" + str(number): x})
                            )
                        )(number)
                    ),
                )

    def cmd_unbind(self, sender_eui64=None, target=None):
        """Unsubscribe to updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64

        if target is None:
            for unsubscribe in self._binds["pump_temp"].values():
                unsubscribe()
            self._binds["pump_temp"] = {}
        elif target in self._binds["pump_temp"]:
            self._binds["pump_temp"].pop(target)()

        if target is None:
            for unsubscribe in self._binds["pump"].values():
                unsubscribe()
            self._binds["pump"] = {}
        elif target in self._binds["pump"]:
            self._binds["pump"].pop(target)()

        for number in range(4):
            if target is None:
                if number in self._binds["valve"]:
                    for unsubscribe in self._binds["valve"][number].values():
                        unsubscribe()
                    self._binds["valve"][number] = {}
            elif (
                number in self._binds["valve"]
                and target in self._binds["valve"][number]
            ):
                self._binds["valve"][number].pop(target)()

        for number in range(3):
            if target is None:
                if number in self._binds["hum"]:
                    for (unsubscribe_available, unsubscribe_zone,) in self._binds[
                        "hum"
                    ][number].values():
                        unsubscribe_available()
                        unsubscribe_zone()
                    self._binds["hum"][number] = {}
            elif number in self._binds["hum"] and target in self._binds["hum"][number]:
                unsubscribe_available, unsubscribe_zone = self._binds["hum"][
                    number
                ].pop(target)
                unsubscribe_available()
                unsubscribe_zone()
