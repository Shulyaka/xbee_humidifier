"""Adds support for xbee_humidifier units."""
from __future__ import annotations

import logging

from homeassistant.components.humidifier import (
    ATTR_HUMIDITY,
    MODE_AWAY,
    MODE_NORMAL,
    HumidifierAction,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityDescription,
    HumidifierEntityFeature,
)
from homeassistant.const import ATTR_MODE, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.restore_state import RestoreEntity

from . import (
    CONF_AWAY_HUMIDITY,
    CONF_MAX_HUMIDITY,
    CONF_MIN_HUMIDITY,
    CONF_SENSOR,
    CONF_TARGET_HUMIDITY,
)
from .const import DOMAIN
from .entity import XBeeHumidifierEntity

_LOGGER = logging.getLogger(__name__)

ATTR_SAVED_HUMIDITY = "saved_humidity"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the humidifier platform."""
    humidifiers = []
    coordinator = hass.data[DOMAIN][entry.entry_id]
    for number in range(0, 3):
        config = entry.options["humidifier_" + str(number)]
        sensor_entity_id = config[CONF_SENSOR]
        target_humidity = config.get(CONF_TARGET_HUMIDITY)
        away_humidity = config.get(CONF_AWAY_HUMIDITY)
        min_humidity = config.get(CONF_MIN_HUMIDITY)
        max_humidity = config.get(CONF_MAX_HUMIDITY)
        entity_description = HumidifierEntityDescription(
            key="xbee_humidifier_" + str(number + 1),
            name="Humidifier",
            has_entity_name=True,
            icon="mdi:air-humidifier",
            device_class=HumidifierDeviceClass.HUMIDIFIER,
        )
        humidifiers.append(
            XBeeHumidifier(
                entity_description,
                coordinator,
                number,
                sensor_entity_id,
                target_humidity,
                away_humidity,
                min_humidity,
                max_humidity,
            )
        )

    async_add_entities(humidifiers)


class XBeeHumidifier(XBeeHumidifierEntity, HumidifierEntity, RestoreEntity):
    """Representation of an XBee Humidifier device."""

    def __init__(
        self,
        entity_description,
        coordinator,
        number,
        sensor_entity_id=None,
        target_humidity=50,
        away_humidity=35,
        min_humidity=None,
        max_humidity=None,
    ):
        """Initialize the hygrostat."""
        self.entity_description = entity_description
        self._attr_unique_id = coordinator.unique_id + "humidifier" + str(number)
        super().__init__(coordinator, number)
        self._number = number
        self._sensor_entity_id = sensor_entity_id
        self._saved_target_humidity = away_humidity
        self._active = False
        self._target_humidity = target_humidity
        self._attr_supported_features = 0
        if away_humidity:
            self._attr_supported_features |= HumidifierEntityFeature.MODES
        self._is_away = False
        self._state = False
        self._min_humidity = min_humidity
        self._max_humidity = max_humidity
        self._remove_sensor_tracking = None
        self._cur_humidity = None

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        if self.coordinator.data.get(self._number)["cur_hum"] is not None:
            self._handle_coordinator_update()
        else:
            if (old_state := await self.async_get_last_state()) is not None:
                if (
                    self._saved_target_humidity is not None
                    and old_state.attributes.get(ATTR_MODE) == MODE_AWAY
                ):
                    self._is_away = True
                    self._target_humidity, self._saved_target_humidity = (
                        self._saved_target_humidity,
                        self._target_humidity,
                    )
                if old_state.attributes.get(ATTR_HUMIDITY):
                    self._target_humidity = int(old_state.attributes[ATTR_HUMIDITY])
                if (
                    self._saved_target_humidity is not None
                    and old_state.attributes.get(ATTR_SAVED_HUMIDITY)
                ):
                    self._saved_target_humidity = int(
                        old_state.attributes[ATTR_SAVED_HUMIDITY]
                    )
                if old_state.state:
                    self._state = old_state.state == STATE_ON

            await self._update_device()

        if self._sensor_entity_id is not None:
            sensor_state = self.hass.states.get(self._sensor_entity_id)
            if sensor_state is not None and sensor_state.state not in (
                STATE_UNKNOWN,
                STATE_UNAVAILABLE,
            ):
                await self._async_sensor_changed(
                    self._sensor_entity_id, None, sensor_state
                )

            # Add listener
            if self._remove_sensor_tracking is None:
                self._remove_sensor_tracking = async_track_state_change(
                    self.hass, self._sensor_entity_id, self._async_sensor_changed
                )
                self.async_on_remove(self._remove_sensor_tracking)

        async def async_log(data):
            if data["msg"] == "Not initialized":
                await self._update_device()

        self.async_on_remove(self.coordinator.client.add_subscriber("log", async_log))

        async def async_update_available(value):
            self._active = value
            return self.async_write_ha_state()

        self.async_on_remove(
            self.coordinator.client.add_subscriber(
                "available_" + str(self._number), async_update_available
            )
        )

        self._attr_action = (
            HumidifierAction.HUMIDIFYING
            if self.coordinator.data.get(self._number, {}).get("working")
            else HumidifierAction.IDLE
        )

        async def async_update_action(value):
            self._attr_action = (
                HumidifierAction.HUMIDIFYING if value else HumidifierAction.IDLE
            )
            self.async_schedule_update_ha_state()

        self.async_on_remove(
            self.coordinator.client.add_subscriber(
                "working_" + str(self._number), async_update_action
            )
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        resp = self.coordinator.data.get(self._number)

        self._state = resp["is_on"]
        self._is_away = resp["mode"] == "away"
        self._target_humidity = resp["target_hum"]
        if self._saved_target_humidity is not None:
            self._saved_target_humidity = resp["sav_hum"]
        self._active = resp["available"]
        self._attr_action = (
            HumidifierAction.HUMIDIFYING if resp["working"] else HumidifierAction.IDLE
        )
        if self._sensor_entity_id is None:
            self._cur_humidity = resp["cur_hum"]

        self.async_write_ha_state()

    async def _update_device(self):
        if self._is_away:
            await self.coordinator.client.async_command(
                "mode", self._number, MODE_NORMAL
            )
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._saved_target_humidity
            )
            await self.coordinator.client.async_command("mode", self._number, MODE_AWAY)
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._target_humidity
            )
        elif self._saved_target_humidity is not None:
            await self.coordinator.client.async_command("mode", self._number, MODE_AWAY)
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._saved_target_humidity
            )
            await self.coordinator.client.async_command(
                "mode", self._number, MODE_NORMAL
            )
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._target_humidity
            )
        else:
            await self.coordinator.client.async_command(
                "mode", self._number, MODE_NORMAL
            )
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._target_humidity
            )
        await self.coordinator.client.async_command("hum", self._number, self._state)

    @callback
    async def _async_startup(self):
        """Init on startup."""

    @property
    def available(self):
        """Return True if entity is available."""
        return self._active and super().available

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        if self._saved_target_humidity:
            return {ATTR_SAVED_HUMIDITY: self._saved_target_humidity}
        return None

    @property
    def is_on(self):
        """Return true if the hygrostat is on."""
        return self._state

    @property
    def current_humidity(self):
        """Return the measured humidity."""
        return self._cur_humidity

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return self._target_humidity

    @property
    def mode(self):
        """Return the current mode."""
        if self._saved_target_humidity is None:
            return None
        if self._is_away:
            return MODE_AWAY
        return MODE_NORMAL

    @property
    def available_modes(self):
        """Return a list of available modes."""
        if self._saved_target_humidity is None:
            return None
        return [MODE_NORMAL, MODE_AWAY]

    @property
    def device_class(self):
        """Return the device class of the humidifier."""
        return HumidifierDeviceClass.HUMIDIFIER

    async def async_turn_on(self, **kwargs):
        """Turn hygrostat on."""
        if (
            await self.coordinator.client.async_command("hum", self._number, True)
            == "OK"
        ):
            self._state = True
        return self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn hygrostat off."""
        if (
            await self.coordinator.client.async_command("hum", self._number, False)
            == "OK"
        ):
            self._state = False
        return self.async_write_ha_state()

    async def async_set_humidity(self, humidity: int):
        """Set new target humidity."""
        if humidity is None:
            return None
        if (
            await self.coordinator.client.async_command(
                "target_hum", self._number, humidity
            )
            == "OK"
        ):
            self._target_humidity = humidity
        return self.async_write_ha_state()

    @property
    def min_humidity(self):
        """Return the minimum humidity."""
        if self._min_humidity:
            return self._min_humidity

        return super().min_humidity

    @property
    def max_humidity(self):
        """Return the maximum humidity."""
        if self._max_humidity:
            return self._max_humidity

        return super().max_humidity

    async def _async_sensor_changed(self, entity_id, old_state, new_state):
        """Handle ambient humidity changes."""
        if new_state is None:
            return None

        try:
            self._cur_humidity = float(new_state.state)
        except ValueError as ex:
            _LOGGER.warning("Unable to update from sensor: %s", ex)
            self._cur_humidity = new_state.state

        await self.coordinator.client.async_command(
            "cur_hum", self._number, self._cur_humidity
        )
        return self.async_write_ha_state()

    async def async_set_mode(self, mode: str):
        """Set new mode."""
        if self._saved_target_humidity is None:
            return None

        if (
            await self.coordinator.client.async_command("mode", self._number, mode)
            == "OK"
        ):
            if self._is_away != (mode == MODE_AWAY):
                self._target_humidity, self._saved_target_humidity = (
                    self._saved_target_humidity,
                    self._target_humidity,
                )
            self._is_away = mode == MODE_AWAY
        return self.async_write_ha_state()
