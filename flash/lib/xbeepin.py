"""Interface to the XBee pins with as core.Entity classes."""

from lib.core import Entity
from machine import ADC, PWM, Pin


class DigitalOutput(Entity):
    """Digital output switch."""

    _cache = True
    _type = bool

    def __init__(self, gpio):
        """Init the class."""
        self._pin = Pin(gpio, Pin.OUT)
        super().__init__()

    def _get(self):
        """Get pin state."""
        return self._pin.value()

    def _set(self, value):
        """Set pin state."""
        self._pin.value(value)


class DigitalInput(Entity):
    """Digital input sensor."""

    _readonly = True
    _type = bool

    def __init__(self, gpio, pull=Pin.PULL_UP, period=500):
        """Init the class."""
        self._pin = Pin(gpio, Pin.IN, pull)
        super().__init__(period=period)

    def _get(self):
        """Get pin state."""
        return self._pin.value()


class AnalogOutput(Entity):
    """PWM output."""

    _cache = True

    def __init__(self, gpio):
        """Init the class."""
        self._pin = PWM(gpio)
        super().__init__()

    def _get(self):
        """Get PWM value."""
        return self._pin.duty()

    def _set(self, value):
        """Set PWM value."""
        self._pin.duty(value)


class AnalogInput(Entity):
    """ADC Input."""

    _readonly = True

    def __init__(self, gpio, period=500, threshold=1):
        """Init the class."""
        self._pin = ADC(gpio)
        super().__init__(period=period, threshold=threshold)

    def _get(self):
        """Get pin state."""
        return self._pin.read()
