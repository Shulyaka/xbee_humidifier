"""Interface to tosr0x relays with as core.Entity classes."""

import logging

from core import Entity
from mainloop import main_loop
from tosr0x import Tosr0x

try:
    tosr = Tosr0x()
except Exception as e:
    from sys import stdout

    stdout.buffer.write("n")
    logging.getLogger(__name__).error("Exception: %s", e)
    raise e


class TosrSwitch(Entity):
    """TOSR0X relay."""

    def __init__(self, switch_number, period=30000):
        """Init the class."""
        super().__init__()
        self._switch_number = switch_number
        self._state = self.state
        self._stop_updates = main_loop.schedule_task(
            lambda: self.update(), period=period
        )

    @property
    def state(self):
        """Get cached relay state."""
        return tosr.get_relay_state(self._switch_number)

    @state.setter
    def state(self, value):
        """Set relay state."""
        value = bool(value)
        tosr.set_relay_state(self._switch_number, value)
        if self._state != value:
            self._state = value
            self._run_triggers(value)

    def update(self):
        """Get relay states."""
        super().update()
        tosr.update()
        value = self.state
        if self._state != value:
            self._state = value
            self._run_triggers(value)


class TosrTemp(Entity):
    """TOSR0X-T temperature sensor."""

    _value = None
    _last_callback_value = None
    _threshold = 0

    def __init__(self, period=30000, threshold=1 / 16):
        """Init the class."""
        super().__init__()
        self._threshold = threshold
        self.update()
        self._stop_updates = main_loop.schedule_task(
            lambda: self.update(auto=True), period=period
        )

    def update(self, auto=None):
        """Get current temperature."""
        super().update()
        value = tosr.temperature
        self._value = value
        threshold = self._threshold if auto else 1 / 16
        if (
            self._last_callback_value is None
            or abs(self._last_callback_value - value) >= threshold
        ):
            self._last_callback_value = value
            self._run_triggers(value)

    @property
    def state(self):
        """Get cached temperature."""
        return self._value

    @state.setter
    def state(self, value):
        """Output is disabled."""
        pass


tosr_switch = {x: TosrSwitch(x) for x in range(5)}
tosr_temp = TosrTemp()
