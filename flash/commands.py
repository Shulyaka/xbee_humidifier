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
        sensor,
        available,
        zone,
        pump,
        pump_block,
    ):
        """Init the module."""
        super().__init__()
        self._valve = valve
        self._pump_temp = pump_temp
        self._humidifier = humidifier
        self._sensor = sensor
        self._available = available
        self._zone = zone
        self._pump = pump
        self._pump_block = pump_block

        self._binds = {
            "pump": {},
            "pump_temp": {},
            "available": {0: {}, 1: {}, 2: {}},
            "zone": {0: {}, 1: {}, 2: {}},
            "valve": {0: {}, 1: {}, 2: {}, 3: {}},
        }

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
                "available": self._available[number].state,
                "is_on": self._humidifier[number].state,
                "working": self._zone[number].state,
                "cap_attr": self._humidifier[number].capability_attributes,
                "state_attr": self._humidifier[number].state_attributes,
                "extra_state_attr": self._humidifier[number].extra_state_attributes,
                "cur_hum": self._sensor[number].state,
            }

        if is_on is not None:
            self._humidifier[number].state = is_on
        if working is not None:
            self._zone[number].state = working
        if mode is not None:
            self._humidifier[number].set_mode(mode)
        if hum is not None:
            self._humidifier[number].set_humidity(hum)
        if cur_hum is not None:
            self._sensor[number].state = cur_hum

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

        def bind(entity, binds, name):
            if target not in binds:
                binds[target] = entity.subscribe(
                    lambda x: self._transmit(target, json_dumps({name: x}))
                )

        bind(self._pump_temp, self._binds["pump_temp"], "pump_temp")
        bind(self._pump, self._binds["pump"], "pump")
        for number in range(4):
            bind(
                self._valve[number],
                self._binds["valve"][number],
                "valve_" + str(number),
            )

        for number in range(3):
            bind(
                self._available[number],
                self._binds["available"][number],
                "available_" + str(number),
            )
            bind(
                self._zone[number],
                self._binds["zone"][number],
                "working_" + str(number),
            )

    def cmd_unbind(self, sender_eui64=None, target=None):
        """Unsubscribe to updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64

        def unbind(binds):
            if target is None:
                for unbind in binds.values():
                    unbind()
                binds.clear()
            elif target in binds:
                binds.pop(target)()

        unbind(self._binds["pump_temp"])
        unbind(self._binds["pump"])
        for number in range(4):
            unbind(self._binds["valve"][number])

        for number in range(3):
            unbind(self._binds["available"][number])
            unbind(self._binds["zone"][number])
