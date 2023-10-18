"""Module defines remote commands."""

from json import dumps as json_dumps

import config
from lib.core import Commands


class HumidifierCommands(Commands):
    """Define application remote commands."""

    def __init__(
        self,
        humidifier,
        sensor,
        available,
        zone,
        pump_block,
    ):
        """Init the module."""
        super().__init__()
        self._humidifier = humidifier
        self._sensor = sensor
        self._available = available
        self._zone = zone
        self._pump_block = pump_block

        self._binds = {
            "pump": {},
            "pump_temp": {},
            "pressure_in": {},
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
    ):
        """Get or set the humidifier state."""
        if is_on is None:
            return {
                "available": self._available[number].state,
                "is_on": self._humidifier[number].state,
                "working": self._zone[number].state,
                "cap_attr": self._humidifier[number].capability_attributes,
                "extra_state_attr": self._humidifier[number].extra_state_attributes,
            }

        if is_on is not None:
            self._humidifier[number].state = is_on
        return "OK"

    def cmd_target_hum(self, sender_eui64, number, hum=None):
        """Get or set target humidity."""
        if hum is None:
            return self._humidifier[number].humidity
        self._humidifier[number].humidity = hum
        return "OK"

    def cmd_mode(self, sender_eui64, number, mode=None):
        """Get or set humidifier mode."""
        if mode is None:
            return self._humidifier[number].mode
        self._humidifier[number].mode = mode
        return "OK"

    def cmd_cur_hum(self, sender_eui64, number, state=None):
        """Get or set current humidity."""
        if state is None:
            return self._sensor[number].state
        self._sensor[number].state = state
        return "OK"

    def cmd_pressure_in(self, sender_eui64=None):
        """Get current inbound pressure."""
        return config.pressure_in.state

    def cmd_pump(self, sender_eui64=None, state=None):
        """Get or set the pump state."""
        if state is None:
            return config.pump.state
        config.pump.state = state
        return "OK"

    def cmd_pump_block(self, sender_eui64=None, state=None):
        """Get or set the status of pump block."""
        if state is None:
            return self._pump_block.state
        self._pump_block.state = state
        return "OK"

    def cmd_pump_speed(self, sender_eui64=None, state=None):
        """Get or set the pump speed."""
        if state is None:
            return config.pump_speed.state
        config.pump_speed.state = state
        return "OK"

    def cmd_fan(self, sender_eui64=None, state=None):
        """Get or set the fan state."""
        if state is None:
            return config.fan.state
        config.fan.state = state
        return "OK"

    def cmd_aux_led(self, sender_eui64=None, state=None):
        """Get or set the AUX LED state."""
        if state is None:
            return config.aux_led.state
        config.aux_led.state = state
        return "OK"

    def cmd_pump_temp(self, sender_eui64=None):
        """Get current pump temperature."""
        return config.pump_temp.state

    def cmd_valve(self, sender_eui64, number, state=None):
        """Get or set the current valve status."""
        if state is None:
            return config.valve_switch[number].state
        config.valve_switch[number].state = state
        return "OK"

    def cmd_bind(self, sender_eui64, target=None):
        """Subscribe to updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64

        def bind(entity, binds, name):
            if target not in binds:
                binds[target] = entity.subscribe(
                    lambda x: self._transmit(target, json_dumps({name: x}))
                )

        bind(config.pump_temp, self._binds["pump_temp"], "pump_temp")
        bind(config.pump, self._binds["pump"], "pump")
        bind(config.pressure_in, self._binds["pressure_in"], "pressure_in")
        for number in range(4):
            bind(
                config.valve_switch[number],
                self._binds["valve"][number],
                "valve_{}".format(number),
            )

        for number in range(3):
            bind(
                self._available[number],
                self._binds["available"][number],
                "available_{}".format(number),
            )
            bind(
                self._zone[number],
                self._binds["zone"][number],
                "working_{}".format(number),
            )
        return "OK"

    def cmd_unbind(self, sender_eui64=None, target=None):
        """Unsubscribe to updates."""
        target = bytes(target, encoding="utf-8") if target is not None else sender_eui64

        def unbind(entity, binds):
            if target is None:
                for bind in binds.values():
                    entity.unsubscribe(bind)
                binds.clear()
            elif target in binds:
                entity.unsubscribe(binds.pop(target))

        unbind(config.pump_temp, self._binds["pump_temp"])
        unbind(config.pump, self._binds["pump"])
        unbind(config.pressure_in, self._binds["pressure_in"])
        for number in range(4):
            unbind(config.valve_switch[number], self._binds["valve"][number])

        for number in range(3):
            unbind(self._available[number], self._binds["available"][number])
            unbind(self._zone[number], self._binds["zone"][number])
        return "OK"
