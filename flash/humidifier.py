"""Generic hygrostat implementation."""

from time import ticks_add, ticks_diff, ticks_ms

from lib import logging
from lib.core import Switch
from lib.mainloop import main_loop

_LOGGER = logging.getLogger(__name__)

_MODE_NORMAL = "normal"
_MODE_AWAY = "away"


class GenericHygrostat(Switch):
    """Representation of a Generic Hygrostat device."""

    def __init__(
        self,
        switch,
        sensor,
        available_sensor,
        min_humidity=0,
        max_humidity=100,
        target_humidity=None,
        dry_tolerance=3,
        wet_tolerance=3,
        initial_state=None,
        away_humidity=None,
        sensor_stale_duration=None,
        *args,
        **kwargs
    ):
        """Initialize the hygrostat."""
        self._switch = switch
        self._sensor = sensor
        self._dry_tolerance = dry_tolerance
        self._wet_tolerance = wet_tolerance
        self._saved_humidity = away_humidity or target_humidity
        self._active = available_sensor
        self._active.state = False
        self._cur_humidity = None
        self._min_humidity = min_humidity
        self._max_humidity = max_humidity
        self._target_humidity = target_humidity
        self._away_humidity = away_humidity
        self._stale_duration = sensor_stale_duration
        self._stale_tracking = None
        self._is_away = False
        super().__init__(
            value=initial_state if initial_state is not None else False, *args, **kwargs
        )

        self._operate_task = None
        self._state_subscriber = self.subscribe(
            lambda x: self._schedule_operate(force=True)
        )

        if self._target_humidity is None:
            self._target_humidity = self._min_humidity
            _LOGGER.warning(
                "No previously saved humidity, setting to {}".format(
                    self._target_humidity
                )
            )

        self._sensor_subscriber = self._sensor.subscribe(
            lambda x: self._sensor_changed(x)
        )

        self._sensor_changed(self._sensor.state)

    def __del__(self):
        """Cancel callbacks."""
        self.unsubscribe(self._state_subscriber)
        self._sensor.unsubscribe(self._sensor_subscriber)
        main_loop.remove_task(self._stale_tracking)
        main_loop.remove_task(self._operate_task)

    def _sensor_changed(self, new_state):
        """Handle ambient humidity changes."""
        if new_state is None:
            return

        if self._stale_duration:
            main_loop.remove_task(self._stale_tracking)
            self._stale_tracking = main_loop.schedule_task(
                lambda: self._sensor_not_responding(),
                ticks_add(ticks_ms(), self._stale_duration * 1000),
            )

        self._update_humidity(new_state)
        self._schedule_operate()

    def _sensor_not_responding(self):
        """Handle sensor stale event."""
        _LOGGER.debug(
            "Sensor has not been updated for %s seconds",
            int(ticks_diff(ticks_ms(), self._sensor_last_updated) / 1000),
        )
        _LOGGER.warning("Sensor is stalled, call the emergency stop")
        self._update_humidity("Stalled")

    def _update_humidity(self, humidity):
        """Update hygrostat with latest state from sensor."""
        try:
            self._cur_humidity = float(humidity)
            self._sensor_last_updated = ticks_ms()
        except ValueError as ex:
            _LOGGER.warning("{}: {}: {}".format(type(ex).__name__, ex, humidity))
            self._cur_humidity = None
            self._active.state = False
            if self._switch.state:
                self._switch.state = False

    def _schedule_operate(self, force=False):
        if self._operate_task:
            if not force:
                return
            main_loop.remove_task(self._operate_task)
        self._operate_task = main_loop.schedule_task(lambda: self._operate(force))

    def _operate(self, force=False):
        """Check if we need to turn humidifying on or off."""
        if self._operate_task:
            main_loop.remove_task(self._operate_task)
            self._operate_task = None

        if not self._active.state and None not in (
            self._cur_humidity,
            self._target_humidity,
        ):
            self._active.state = True
            force = True
            _LOGGER.info(
                "Obtained current and target humidity. "
                "Generic hygrostat active. {}, {}".format(
                    self._cur_humidity, self._target_humidity
                )
            )

        if not self._active.state or not self._state:
            if force:
                self._switch.state = False
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
        if self._switch.state:
            if too_wet:
                self._switch.state = False
        else:
            if too_dry:
                self._switch.state = True

    @property
    def attributes(self):
        """Return attributes."""
        return {
            "min_hum": self._min_humidity,
            "max_hum": self._max_humidity,
            "sav_hum": self._saved_humidity,
        }

    @property
    def humidity(self):
        """Return the target humidity."""
        return self._target_humidity

    @humidity.setter
    def humidity(self, humidity):
        """Set new target humidity."""
        self._target_humidity = int(humidity)
        self._schedule_operate()

    @property
    def mode(self):
        """Return the current mode."""
        if self._away_humidity is None:
            return None
        if self._is_away:
            return _MODE_AWAY
        return _MODE_NORMAL

    @mode.setter
    def mode(self, mode: str):
        """Set new mode."""
        if self._away_humidity is None:
            return
        if mode == _MODE_AWAY and not self._is_away:
            self._is_away = True
            if not self._saved_humidity:
                self._saved_humidity = self._away_humidity
            self._saved_humidity, self._target_humidity = (
                self._target_humidity,
                self._saved_humidity,
            )
            self._schedule_operate(force=True)
        elif mode == _MODE_NORMAL and self._is_away:
            self._is_away = False
            self._saved_humidity, self._target_humidity = (
                self._target_humidity,
                self._saved_humidity,
            )
            self._schedule_operate(force=True)
