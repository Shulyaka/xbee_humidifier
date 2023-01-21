"""Interface to tosr0x relays with as core.Entity classes."""

from lib import logging
from lib.core import Entity
from lib.mainloop import main_loop
from lib.tosr0x import Tosr0x

try:
    tosr = Tosr0x()
except Exception as e:
    Tosr0x.tosr0x_reset()
    logging.getLogger(__name__).error("Exception: %s: %s", type(e).__name__, e)
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

    def __del__(self):
        """Cancel callbacks."""
        self._stop_updates()

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

    def __init__(self, period=30000, threshold=1 / 16):
        """Init the class."""
        super().__init__()
        self._last_callback_value = None
        self._threshold = threshold
        self.update()
        self._stop_updates = main_loop.schedule_task(
            lambda: self.update(auto=True), period=period
        )

    def __del__(self):
        """Cancel callbacks."""
        self._stop_updates()

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
