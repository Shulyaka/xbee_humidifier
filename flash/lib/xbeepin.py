"""Interface to the XBee pins with as core.Entity classes."""

from core import Entity
from machine import ADC, PWM, Pin
from mainloop import main_loop


class DigitalOutput(Entity):
    """Digital output switch."""

    _pin = None

    def __init__(self, gpio):
        """Init the class."""
        super().__init__()
        self._pin = Pin(gpio, Pin.OUT)

    @property
    def state(self):
        """Get pin state."""
        return bool(self._pin.value())

    @state.setter
    def state(self, value):
        """Set pin state."""
        self._pin.value(value)
        self._run_triggers(bool(value))


class DigitalInput(Entity):
    """Digital input sensor."""

    _pin = None
    _value = None

    def __init__(self, gpio, pull=None, period=500):
        """Init the class."""
        super().__init__()
        self._pin = Pin(gpio, Pin.IN, pull)
        self.update()
        self._stop_updates = main_loop.schedule_task(
            lambda: self.update(), period=period
        )

    def __del__(self):
        """Cancel callbacks."""
        self._stop_updates()

    def update(self):
        """Get pin state."""
        super().update()
        value = bool(self._pin.value())
        if self._value != value:
            self._value = value
            self._run_triggers(value)

    @property
    def state(self):
        """Get cached state."""
        return self._value

    @state.setter
    def state(self, value):
        """Output is disabled."""
        pass


class AnalogOutput(Entity):
    """PWM output."""

    _pin = None

    def __init__(self, gpio):
        """Init the class."""
        super().__init__()
        self._pin = PWM(gpio)

    @property
    def state(self):
        """Get PWM value."""
        return self._pin.duty()

    @state.setter
    def state(self, value):
        """Set PWM value."""
        self._pin.duty(value)
        self._run_triggers(value)


class AnalogInput(Entity):
    """ADC Input."""

    _pin = None
    _value = None
    _last_callback_value = None
    _threshold = 0

    def __init__(self, gpio, period=500, threshold=1):
        """Init the class."""
        super().__init__()
        self._pin = ADC(gpio)
        self._threshold = threshold
        self.update()
        self._stop_updates = main_loop.schedule_task(
            lambda: self.update(auto=True), period=period
        )

    def __del__(self):
        """Cancel callbacks."""
        self._stop_updates()

    def update(self, auto=None):
        """Get pin state."""
        super().update()
        value = self._pin.read()
        self._value = value
        threshold = self._threshold if auto else 1
        if (
            self._last_callback_value is None
            or abs(self._last_callback_value - value) >= threshold
        ):
            self._last_callback_value = value
            self._run_triggers(value)

    @property
    def state(self):
        """Get cached state."""
        return self._value

    @state.setter
    def state(self, value):
        """Output is disabled."""
        pass
