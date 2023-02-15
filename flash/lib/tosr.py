"""Interface to tosr0x relays with as core.Entity classes."""

from lib import logging
from lib.core import Entity
from lib.tosr0x import Tosr0x

try:
    tosr = Tosr0x()
except Exception as e:
    Tosr0x.tosr0x_reset()
    logging.getLogger(__name__).error("Exception: %s: %s", type(e).__name__, e)
    raise e


class TosrSwitch(Entity):
    """TOSR0X relay."""

    _type = bool

    def __init__(self, switch_number, period=30000):
        """Init the class."""
        self._switch_number = switch_number
        super().__init__(value=None, period=period)

    def _get(self):
        """Get relay state."""
        tosr.update()
        return tosr.get_relay_state(self._switch_number)

    def _set(self, value):
        """Set relay state."""
        tosr.set_relay_state(self._switch_number, value)


class TosrTemp(Entity):
    """TOSR0X-T temperature sensor."""

    _readonly = True

    def __init__(self, period=30000, threshold=1 / 16):
        """Init the class."""
        super().__init__(period=period, threshold=threshold)

    def _get(self):
        return tosr.temperature


tosr_switch = {x: TosrSwitch(x + 1) for x in range(4)}
tosr_temp = TosrTemp()
