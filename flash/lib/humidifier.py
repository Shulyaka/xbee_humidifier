"""Generic hygrostat implementation."""

from time import ticks_ms

from lib import logging
from lib.core import Entity
from lib.mainloop import main_loop
from micropython import const

_LOGGER = logging.getLogger(__name__)

ATTR_HUMIDITY = const("hum")
ATTR_MAX_HUMIDITY = const("max_hum")
ATTR_MIN_HUMIDITY = const("min_hum")
ATTR_SAVED_HUMIDITY = const("sav_hum")
ATTR_MODE = const("mode")

MODE_NORMAL = const("normal")
MODE_AWAY = const("away")


class GenericHygrostat(Entity):
    """Representation of a Generic Hygrostat device."""

    def __init__(
        self,
        switch_entity_id,
        sensor_entity_id,
        available_sensor_id,
        min_humidity=0,
        max_humidity=100,
        target_humidity=None,
        dry_tolerance=3,
        wet_tolerance=3,
        initial_state=None,
        away_humidity=None,
        sensor_stale_duration=None,
    ):
        """Initialize the hygrostat."""
        super().__init__()
        self._switch_entity_id = switch_entity_id
        self._sensor_entity_id = sensor_entity_id
        self._dry_tolerance = dry_tolerance
        self._wet_tolerance = wet_tolerance
        self._state = initial_state if initial_state is not None else False
        self._saved_target_humidity = away_humidity or target_humidity
        self._active = available_sensor_id
        self._active.state = False
        self._cur_humidity = None
        self._min_humidity = min_humidity
        self._max_humidity = max_humidity
        self._target_humidity = target_humidity
        self._away_humidity = away_humidity
        self._sensor_stale_duration = sensor_stale_duration
        self._remove_stale_tracking = None
        self._is_away = False

        if self._target_humidity is None:
            self._target_humidity = self._min_humidity
            _LOGGER.warning(
                "No previously saved humidity, setting to %s", self._target_humidity
            )

        self._sensor_unsubscribe = self._sensor_entity_id.subscribe(
            lambda x: self._sensor_changed(x)
        )

        self._sensor_changed(self._sensor_entity_id.state)

    def __del__(self):
        """Cancel callbacks."""
        self._sensor_unsubscribe()
        if self._remove_stale_tracking:
            self._remove_stale_tracking()

    @property
    def capability_attributes(self):
        """Return capability attributes."""
        data = {
            ATTR_MIN_HUMIDITY: self._min_humidity,
            ATTR_MAX_HUMIDITY: self._max_humidity,
        }

        return data

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = {}

        if self._target_humidity is not None:
            data[ATTR_HUMIDITY] = self._target_humidity

        data[ATTR_MODE] = self.mode

        return data

    @property
    def state(self):
        """Get current state."""
        return self._state

    @state.setter
    def state(self, value):
        """Set current state."""
        if not self._active.state:
            return
        self._state = bool(value)
        if value:
            self._operate(force=True)
        else:
            if self._switch_entity_id.state:
                self._switch_entity_id.state = False
        self._run_triggers(bool(value))

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        if self._saved_target_humidity:
            return {ATTR_SAVED_HUMIDITY: self._saved_target_humidity}
        return None

    @property
    def mode(self):
        """Return the current mode."""
        if self._away_humidity is None:
            return None
        if self._is_away:
            return MODE_AWAY
        return MODE_NORMAL

    def set_humidity(self, humidity):
        """Set new target humidity."""
        self._target_humidity = int(humidity)
        self._operate()

    def _sensor_changed(self, new_state):
        """Handle ambient humidity changes."""
        if new_state is None:
            return

        if self._sensor_stale_duration:
            if self._remove_stale_tracking:
                self._remove_stale_tracking()
            self._remove_stale_tracking = main_loop.schedule_task(
                lambda: self._sensor_not_responding(),
                ticks_ms() + self._sensor_stale_duration * 1000,
            )

        self._update_humidity(new_state)
        self._operate()

    def _sensor_not_responding(self):
        """Handle sensor stale event."""
        _LOGGER.debug(
            "Sensor has not been updated for %s seconds",
            int((ticks_ms() - self._sensor_last_updated) / 1000),
        )
        _LOGGER.warning("Sensor is stalled, call the emergency stop")
        self._update_humidity("Stalled")

    def _update_humidity(self, humidity):
        """Update hygrostat with latest state from sensor."""
        try:
            self._cur_humidity = float(humidity)
            self._sensor_last_updated = ticks_ms()
        except ValueError as ex:
            _LOGGER.warning("Unable to update from sensor: %s", ex)
            self._cur_humidity = None
            self._active.state = False
            if self._switch_entity_id.state:
                self._switch_entity_id.state = False

    def _operate(self, force=False):
        """Check if we need to turn humidifying on or off."""
        if not self._active.state and None not in (
            self._cur_humidity,
            self._target_humidity,
        ):
            self._active.state = True
            force = True
            _LOGGER.info(
                (
                    "Obtained current and target humidity. "
                    "Generic hygrostat active. %s, %s"
                ),
                self._cur_humidity,
                self._target_humidity,
            )

        if not self._active.state or not self._state:
            return

        if force:
            # Ignore the tolerance when switched on manually
            dry_tolerance = 0
            wet_tolerance = 0
        else:
            dry_tolerance = self._dry_tolerance
            wet_tolerance = self._wet_tolerance

        too_dry = self._target_humidity - self._cur_humidity >= dry_tolerance
        too_wet = self._cur_humidity - self._target_humidity >= wet_tolerance
        if self._switch_entity_id.state:
            if too_wet:
                _LOGGER.debug("Turning off humidifier switch")
                self._switch_entity_id.state = False
        else:
            if too_dry:
                _LOGGER.debug("Turning on humidifier switch")
                self._switch_entity_id.state = True

    def set_mode(self, mode: str):
        """Set new mode."""
        if self._away_humidity is None:
            return
        if mode == MODE_AWAY and not self._is_away:
            self._is_away = True
            if not self._saved_target_humidity:
                self._saved_target_humidity = self._away_humidity
            self._saved_target_humidity, self._target_humidity = (
                self._target_humidity,
                self._saved_target_humidity,
            )
            self._operate(force=True)
        elif mode == MODE_NORMAL and self._is_away:
            self._is_away = False
            self._saved_target_humidity, self._target_humidity = (
                self._target_humidity,
                self._saved_target_humidity,
            )
            self._operate(force=True)
