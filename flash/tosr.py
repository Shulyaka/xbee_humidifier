"""Interface to tosr0x relays with as core.Sensor classes."""

from lib import logging
from lib.core import Sensor
from tosr0x import Tosr0x

try:
    _tosr = Tosr0x()
except Exception as e:
    Tosr0x.tosr0x_reset()
    logging.getLogger(__name__).error("{}: {}".format(type(e).__name__, e))
    raise e


class TosrSwitch(Sensor):
    """TOSR0X relay."""

    _type = bool
    _period = 5000

    def __init__(self, switch_number, *args, **kwargs):
        """Init the class."""
        self._switch_number = switch_number
        super().__init__(*args, **kwargs)

    def _get(self):
        """Get relay state."""
        _tosr.update()
        return _tosr.get_relay_state(self._switch_number)

    def _set(self, value):
        """Set relay state."""
        _tosr.set_relay_state(self._switch_number, value)


class TosrTemp(Sensor):
    """TOSR0X-T temperature sensor."""

    _readonly = True
    _period = 30000
    _lowpass = 1875

    def _get(self):
        """Get the temperature."""
        return _tosr.temperature


tosr_switch = [TosrSwitch(x + 1) for x in range(4)]
tosr_temp = TosrTemp()
