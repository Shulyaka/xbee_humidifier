"""Adds support for xbee_humidifier units."""
from __future__ import annotations

import logging

from homeassistant.components.humidifier import (
    ATTR_ACTION,
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
        self._attr_saved_target_humidity = away_humidity
        self._attr_target_humidity = target_humidity
        self._attr_available = False
        self._attr_is_on = False
        if away_humidity:
            self._attr_supported_features |= HumidifierEntityFeature.MODES
            self._attr_available_modes = [MODE_NORMAL, MODE_AWAY]
        self._attr_mode = MODE_NORMAL
        if min_humidity is not None:
            self._attr_min_humidity = min_humidity
        if max_humidity is not None:
            self._attr_max_humidity = max_humidity
        self._remove_sensor_tracking = None

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        if (
            self.coordinator.data.get("humidifier", {})
            .get(self._number, {})
            .get("cur_hum")
            is not None
        ):
            self._handle_coordinator_update()
        else:
            if (old_state := await self.async_get_last_state()) is not None:
                if (
                    self._attr_saved_target_humidity is not None
                    and old_state.attributes.get(ATTR_MODE) == MODE_AWAY
                ):
                    self._attr_mode = MODE_AWAY
                    self._attr_target_humidity, self._attr_saved_target_humidity = (
                        self._attr_saved_target_humidity,
                        self._attr_target_humidity,
                    )
                if old_state.attributes.get(ATTR_HUMIDITY) is not None:
                    self._attr_target_humidity = int(
                        old_state.attributes[ATTR_HUMIDITY]
                    )
                if (
                    self._attr_saved_target_humidity is not None
                    and old_state.attributes.get(ATTR_SAVED_HUMIDITY) is not None
                ):
                    self._attr_saved_target_humidity = int(
                        old_state.attributes[ATTR_SAVED_HUMIDITY]
                    )
                if old_state.attributes.get(ATTR_ACTION) is not None:
                    self._attr_action = old_state.attributes[ATTR_ACTION]
                if old_state.state is not None:
                    self._attr_is_on = old_state.state == STATE_ON

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
            if data["msg"] in ("Not initialized", "Main loop started"):
                await self._update_device()

        self.async_on_remove(self.coordinator.client.add_subscriber("log", async_log))

        async def async_update_available(value):
            self._attr_available = value
            return self.async_write_ha_state()

        self.async_on_remove(
            self.coordinator.client.add_subscriber(
                "available_" + str(self._number), async_update_available
            )
        )

        async def async_update_action(value):
            self._attr_action = (
                HumidifierAction.HUMIDIFYING if value else HumidifierAction.IDLE
            )
            self.async_write_ha_state()

        self.async_on_remove(
            self.coordinator.client.add_subscriber(
                "working_" + str(self._number), async_update_action
            )
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        resp = self.coordinator.data.get("humidifier", {}).get(self._number)
        if resp is None:
            return

        self._attr_is_on = resp["is_on"]
        self._attr_mode = resp["mode"]
        self._attr_target_humidity = resp["target_hum"]
        if self._attr_saved_target_humidity is not None:
            self._attr_saved_target_humidity = resp["sav_hum"]
        self._attr_available = resp["available"]
        self._attr_action = (
            HumidifierAction.HUMIDIFYING if resp["working"] else HumidifierAction.IDLE
        )
        if self._sensor_entity_id is None:
            self._attr_current_humidity = resp["cur_hum"]

        self.async_write_ha_state()

    async def _update_device(self):
        if self._attr_mode == MODE_AWAY:
            await self.coordinator.client.async_command(
                "mode", self._number, MODE_NORMAL
            )
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._attr_saved_target_humidity
            )
            await self.coordinator.client.async_command("mode", self._number, MODE_AWAY)
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._attr_target_humidity
            )
        elif self._attr_saved_target_humidity is not None:
            await self.coordinator.client.async_command("mode", self._number, MODE_AWAY)
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._attr_saved_target_humidity
            )
            await self.coordinator.client.async_command(
                "mode", self._number, MODE_NORMAL
            )
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._attr_target_humidity
            )
        else:
            await self.coordinator.client.async_command(
                "mode", self._number, MODE_NORMAL
            )
            await self.coordinator.client.async_command(
                "target_hum", self._number, self._attr_target_humidity
            )
        await self.coordinator.client.async_command(
            "hum", self._number, self._attr_is_on
        )

    @property
    def available(self):
        """Return True if entity is available."""
        return self._attr_available and super().available

    @property
    def extra_state_attributes(self):
        """Return the optional state attributes."""
        if self._attr_saved_target_humidity:
            return {ATTR_SAVED_HUMIDITY: self._attr_saved_target_humidity}
        return None

    async def _turn(self, is_on: bool) -> None:
        """Turn on or off."""
        if (
            await self.coordinator.client.async_command("hum", self._number, is_on)
            == "OK"
        ):
            self._attr_is_on = is_on
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn hygrostat on."""
        await self._turn(True)

    async def async_turn_off(self, **kwargs):
        """Turn hygrostat off."""
        await self._turn(False)

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
            self._attr_target_humidity = humidity
        return self.async_write_ha_state()

    async def _async_sensor_changed(self, entity_id, old_state, new_state):
        """Handle ambient humidity changes."""
        if new_state is None:
            return None

        try:
            self._attr_current_humidity = float(new_state.state)
        except ValueError as ex:
            _LOGGER.warning("Unable to update from sensor: %s", ex)
            self._attr_current_humidity = new_state.state

        await self.coordinator.client.async_command(
            "cur_hum", self._number, self._attr_current_humidity
        )
        return self.async_write_ha_state()

    async def async_set_mode(self, mode: str):
        """Set new mode."""
        if self._attr_saved_target_humidity is None:
            return None

        if (
            await self.coordinator.client.async_command("mode", self._number, mode)
            == "OK"
        ):
            if self._attr_mode != mode:
                self._attr_target_humidity, self._attr_saved_target_humidity = (
                    self._attr_saved_target_humidity,
                    self._attr_target_humidity,
                )
            self._attr_mode = mode
        return self.async_write_ha_state()
