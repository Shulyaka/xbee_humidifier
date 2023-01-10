import logging

_LOGGER = logging.getLogger(__name__)


class Entity:
    def __init__(self):
        self._triggers = []

    def _run_triggers(self, value):
        for callback in self._triggers:
            try:
                callback(value)
            except Exception as e:
                _LOGGER.error(e)

    def subscribe(self, callback):
        self._triggers.append(callback)
        return lambda: self._triggers.remove(callback)

    @property
    def state(self):
        pass

    @state.setter
    def state(self, value):
        self._run_triggers(value)

    def update(self):
        pass


class VirtualSwitch(Entity):
    def __init__(self, value=None):
        super().__init__()
        self._state = bool(value)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = bool(value)
        self._run_triggers(bool(value))


class VirtualSensor(Entity):
    def __init__(self, value=None):
        super().__init__()
        self._state = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self._run_triggers(value)
