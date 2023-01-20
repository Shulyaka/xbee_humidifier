"""Implementation of Entity classes with subscription support."""

from lib import logging

_LOGGER = logging.getLogger(__name__)


class Entity:
    """Base class."""

    def __init__(self):
        """Init the class."""
        self._triggers = []

    def _run_triggers(self, value):
        """Call all defined callbacks one by one synchronically."""
        for callback in self._triggers:
            try:
                callback(value)
            except Exception as e:
                _LOGGER.error(e)

    def subscribe(self, callback):
        """Add new callback."""
        self._triggers.append(callback)
        return lambda: self._triggers.remove(callback)

    @property
    def state(self):
        """Get cached state."""
        pass

    @state.setter
    def state(self, value):
        """Set new state."""
        self._run_triggers(value)

    def update(self):
        """Get updated state."""
        pass


class VirtualSwitch(Entity):
    """Virtual digital entity."""

    def __init__(self, value=None):
        """Init the class."""
        super().__init__()
        self._state = bool(value)

    @property
    def state(self):
        """Get cached state."""
        return self._state

    @state.setter
    def state(self, value):
        """Set new state."""
        self._state = bool(value)
        self._run_triggers(bool(value))


class VirtualSensor(Entity):
    """Virtual numeric entity."""

    def __init__(self, value=None):
        """Init the class."""
        super().__init__()
        self._state = value

    @property
    def state(self):
        """Get cached state."""
        return self._state

    @state.setter
    def state(self, value):
        """Set new state."""
        self._state = value
        self._run_triggers(value)
