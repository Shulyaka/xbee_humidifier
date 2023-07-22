"""Interface to the XBee pins with as core.Sensor classes."""

from lib.core import Sensor
from machine import ADC, PWM, Pin


class DigitalOutput(Sensor):
    """Digital output switch."""

    _cache = True
    _type = bool

    def __init__(self, gpio, *args, **kwargs):
        """Init the class."""
        self._pin = Pin(gpio, Pin.OUT)
        super().__init__(*args, **kwargs)

    def _get(self):
        """Get pin state."""
        return self._pin.value()

    def _set(self, value):
        """Set pin state."""
        self._pin.value(value)


class DigitalInput(Sensor):
    """Digital input sensor."""

    _readonly = True
    _type = bool
    _period = 500

    def __init__(self, gpio, pull=Pin.PULL_UP, *args, **kwargs):
        """Init the class."""
        self._pin = Pin(gpio, Pin.IN, pull)
        super().__init__(*args, **kwargs)

    def _get(self):
        """Get pin state."""
        return self._pin.value()


class AnalogOutput(Sensor):
    """PWM output."""

    _cache = True

    def __init__(self, gpio, *args, **kwargs):
        """Init the class."""
        self._pin = PWM(gpio)
        super().__init__(*args, **kwargs)

    def _get(self):
        """Get PWM value."""
        return self._pin.duty()

    def _set(self, value):
        """Set PWM value."""
        self._pin.duty(value)


class AnalogInput(Sensor):
    """ADC Input."""

    _readonly = True
    _period = 500
    _lowpass = 1000000

    def __init__(self, gpio, *args, **kwargs):
        """Init the class."""
        self._pin = ADC(gpio)
        super().__init__(*args, **kwargs)

    def _get(self):
        """Get pin state."""
        return self._pin.read()
