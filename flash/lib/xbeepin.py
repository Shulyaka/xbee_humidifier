from machine import Pin, PWM, ADC
from core import Entity


class DigitalOutput(Entity):
    _pin = None

    def __init__(self, gpio):
        super().__init__()
        self._pin = Pin(gpio, Pin.OUT)

    @property
    def state(self):
        return bool(self._pin.value())

    @state.setter
    def state(self, value):
        self._pin.value(value)
        self._run_triggers(bool(value))


class DigitalInput(Entity):
    _pin = None
    _value = None

    def __init__(self, gpio, pull=None, period=500):
        super().__init__()
        self._pin = Pin(gpio, Pin.IN, pull)
        self.update()
        self._stop_updates = main_loop.schedule_task(
            lambda: self.update(), period=period
        )

    def update(self):
        super().update()
        value = bool(self._pin.value())
        if self._value != value:
            self._value = value
            self._run_triggers(value)

    @property
    def state(self):
        return self._value

    @state.setter
    def state(self, value):
        pass


class AnalogOutput(Entity):
    _pin = None

    def __init__(self, gpio):
        super().__init__()
        self._pin = PWM(gpio)

    @property
    def state(self):
        return self._pin.duty()

    @state.setter
    def state(self, value):
        self._pin.duty(value)
        self._run_triggers(value)


class AnalogInput(Entity):
    _pin = None
    _value = None
    _threshold = 0

    def __init__(self, gpio, period=500, threshold=0):
        super().__init__()
        self._pin = ADC(gpio)
        self._threshold = threshold
        self.update()
        self._stop_updates = main_loop.schedule_task(
            lambda: self.update(), period=period
        )

    def update(self):
        super().update()
        value = self._pin.read()
        if self._value is None or abs(self._value - value) > self._threshold:
            self._value = value
            self._run_triggers(value)

    @property
    def state(self):
        return self._value

    @state.setter
    def state(self, value):
        pass
