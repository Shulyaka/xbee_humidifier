"""Generic hygrostat implementation."""

import logging
from time import ticks_ms

from core import Entity
from mainloop import main_loop
from micropython import const

_LOGGER = logging.getLogger(__name__)

MODES = const(1)
HUMIDIFIER = const("humidifier")
DEHUMIDIFIER = const("dehumidifier")

ATTR_AVAILABLE_MODES = const("available_modes")
ATTR_HUMIDITY = const("humidity")
ATTR_MAX_HUMIDITY = const("max_humidity")
ATTR_MIN_HUMIDITY = const("min_humidity")
ATTR_SAVED_HUMIDITY = const("saved_humidity")
ATTR_MODE = const("mode")

MODE_NORMAL = const("normal")
# MODE_ECO = const("eco")
MODE_AWAY = const("away")
# MODE_BOOST = const("boost")
# MODE_COMFORT = const("comfort")
# MODE_HOME = const("home")
# MODE_SLEEP = const("sleep")
# MODE_AUTO = const("auto")
# MODE_BABY = const("baby")


class HumidifierEntity(Entity):
    """Base class for humidifier device emulating HA class."""

    def update_ha_state(self):
        """Run triggers on state updates."""
        self._run_triggers(self.state)

    def schedule_update_ha_state(self):
        """Run triggers on state updates."""
        self.update_ha_state()

    @property
    def name(self):
        """Return entity name."""
        pass

    @property
    def min_humidity(self):
        """Return default min humidity."""
        return 0

    @property
    def max_humidity(self):
        """Return default max humidity."""
        return 100

    @property
    def capability_attributes(self):
        """Return capability attributes."""
        supported_features = self._attr_supported_features or 0
        data = {
            ATTR_MIN_HUMIDITY: self.min_humidity,
            ATTR_MAX_HUMIDITY: self.max_humidity,
        }

        if supported_features & MODES:
            data[ATTR_AVAILABLE_MODES] = self.available_modes

        return data

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        supported_features = self._attr_supported_features or 0
        data = {}

        if self.target_humidity is not None:
            data[ATTR_HUMIDITY] = self.target_humidity

        if supported_features & MODES:
            data[ATTR_MODE] = self.mode

        return data

    @property
    def state(self):
        """Get current state."""
        return self.is_on

    @state.setter
    def state(self, value):
        """Set current state."""
        if value:
            self.turn_on()
        else:
            self.turn_off()
        self._run_triggers(value)


class RestoreEntity:
    """Dummy class for compatibility."""

    pass


class GenericHygrostat(HumidifierEntity, RestoreEntity):
    """Representation of a Generic Hygrostat device."""

    def __init__(
        self,
        switch_entity_id,
        sensor_entity_id,
        available_sensor_id,
        name="Generic Hygrostat",
        min_humidity=None,
        max_humidity=None,
        target_humidity=None,
        device_class=None,
        dry_tolerance=3,
        wet_tolerance=3,
        initial_state=None,
        away_humidity=None,
        away_fixed=None,
        sensor_stale_duration=None,
    ):
        """Initialize the hygrostat."""
        super().__init__()
        self._name = name
        self._switch_entity_id = switch_entity_id
        self._sensor_entity_id = sensor_entity_id
        self._device_class = device_class
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
        self._attr_supported_features = MODES if away_humidity else 0
        self._away_humidity = away_humidity
        self._away_fixed = away_fixed
        self._sensor_stale_duration = sensor_stale_duration
        self._remove_stale_tracking = None
        self._is_away = False
        if not self._device_class:
            self._device_class = HUMIDIFIER

        if self._target_humidity is None:
            if self._device_class == HUMIDIFIER:
                self._target_humidity = self.min_humidity
            else:
                self._target_humidity = self.max_humidity
            _LOGGER.warning(
                "No previously saved humidity, setting to %s", self._target_humidity
            )

        self._sensor_unsubscribe = self._sensor_entity_id.subscribe(
            lambda x: self._sensor_changed(None, None, x)
        )
        self._switch_unsubscribe = self._switch_entity_id.subscribe(
            lambda x: self._switch_changed(None, None, x)
        )

        self._sensor_changed(None, None, self._sensor_entity_id.state)

    def __del__(self):
        """Cancel callbacks."""
        self._sensor_unsubscribe()
        self._switch_unsubscribe()
        if self._remove_stale_tracking:
            self._remove_stale_tracking()

    @property
    def available(self):
        """Return True if entity is available."""
        return self._active.state

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        if self._saved_target_humidity:
            return {ATTR_SAVED_HUMIDITY: self._saved_target_humidity}
        return None

    @property
    def name(self):
        """Return the name of the hygrostat."""
        return self._name

    @property
    def is_on(self):
        """Return true if the hygrostat is on."""
        return self._state

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return self._target_humidity

    @property
    def mode(self):
        """Return the current mode."""
        if self._away_humidity is None:
            return None
        if self._is_away:
            return MODE_AWAY
        return MODE_NORMAL

    @property
    def available_modes(self):
        """Return a list of available modes."""
        if self._away_humidity:
            return [MODE_NORMAL, MODE_AWAY]
        return None

    @property
    def device_class(self):
        """Return the device class of the humidifier."""
        return self._device_class

    def turn_on(self, **kwargs):
        """Turn hygrostat on."""
        if not self._active.state:
            return
        self._state = True
        self._operate(force=True)
        self.update_ha_state()

    def turn_off(self, **kwargs):
        """Turn hygrostat off."""
        if not self._active.state:
            return
        self._state = False
        if self._is_device_active:
            self._device_turn_off()
        self.update_ha_state()

    def set_humidity(self, humidity: int):
        """Set new target humidity."""
        if humidity is None:
            return

        if self._is_away and self._away_fixed:
            self._saved_target_humidity = humidity
            self.update_ha_state()
            return

        self._target_humidity = humidity
        self._operate()
        self.update_ha_state()

    @property
    def min_humidity(self):
        """Return the minimum humidity."""
        if self._min_humidity:
            return self._min_humidity

        # get default humidity from super class
        return super().min_humidity

    @property
    def max_humidity(self):
        """Return the maximum humidity."""
        if self._max_humidity:
            return self._max_humidity

        # Get default humidity from super class
        return super().max_humidity

    def _sensor_changed(self, entity_id, old_state, new_state):
        """Handle ambient humidity changes."""
        if new_state is None:
            return

        if self._sensor_stale_duration:
            if self._remove_stale_tracking:
                self._remove_stale_tracking()
            self._remove_stale_tracking = main_loop.schedule_task(
                lambda: self._sensor_not_responding(),
                self._sensor_stale_duration * 1000,
            )

        self._update_humidity(new_state)
        self._operate()
        self.update_ha_state()

    def _sensor_not_responding(self):
        """Handle sensor stale event."""
        _LOGGER.debug(
            "Sensor has not been updated for %s seconds",
            (ticks_ms() - self._sensor_last_updated) / 1000,
        )
        _LOGGER.warning("Sensor is stalled, call the emergency stop")
        self._update_humidity("Stalled")

    def _switch_changed(self, entity_id, old_state, new_state):
        """Handle humidifier switch state changes."""
        if new_state is None:
            return
        self.schedule_update_ha_state()

    def _update_humidity(self, humidity):
        """Update hygrostat with latest state from sensor."""
        try:
            self._cur_humidity = float(humidity)
            self._sensor_last_updated = ticks_ms()
        except ValueError as ex:
            _LOGGER.warning("Unable to update from sensor: %s", ex)
            self._cur_humidity = None
            self._active.state = False
            if self._is_device_active:
                self._device_turn_off()

    def _operate(self, time=None, force=False):
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
        if self._is_device_active:
            if (self._device_class == HUMIDIFIER and too_wet) or (
                self._device_class == DEHUMIDIFIER and too_dry
            ):
                _LOGGER.info("Turning off humidifier %s", self._switch_entity_id)
                self._device_turn_off()
            elif time is not None:
                # The time argument is passed only in keep-alive case
                self._device_turn_on()
        else:
            if (self._device_class == HUMIDIFIER and too_dry) or (
                self._device_class == DEHUMIDIFIER and too_wet
            ):
                _LOGGER.info("Turning on humidifier %s", self._switch_entity_id)
                self._device_turn_on()
            elif time is not None:
                # The time argument is passed only in keep-alive case
                self._device_turn_off()

    @property
    def _is_device_active(self):
        """If the toggleable device is currently active."""
        return self._switch_entity_id.state

    def _device_turn_on(self):
        """Turn humidifier toggleable device on."""
        self._switch_entity_id.state = True

    def _device_turn_off(self):
        """Turn humidifier toggleable device off."""
        self._switch_entity_id.state = False

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

        self.update_ha_state()
