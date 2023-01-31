"""Module defines remote commands."""

from json import dumps as json_dumps

from lib.core import Commands
from xbee import transmit


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

        self._pump_temp_binds = {}
        self._valve_binds = {}
        self._humidifier_binds = {}
        self._pump_binds = {}

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
                        json_dumps({"available_" + str(number): x}),
                    )
                ),
                self._humidifier_zone[number].subscribe(
                    lambda x: transmit(
                        target,
                        json_dumps({"working_" + str(number): x}),
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
