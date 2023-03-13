"""Adds support for xbee_humidifier units."""
from __future__ import annotations

import logging

from homeassistant.components.humidifier import (
    ATTR_HUMIDITY,
    MODE_AWAY,
    MODE_NORMAL,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityDescription,
    HumidifierEntityFeature,
)
from homeassistant.const import (
    ATTR_MODE,
    CONF_NAME,
    EVENT_COMPONENT_LOADED,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.restore_state import RestoreEntity

from . import CONF_AWAY_HUMIDITY, CONF_SENSOR, CONF_TARGET_HUMIDITY
from .const import DOMAIN
from .entity import XBeeHumidifierEntity

_LOGGER = logging.getLogger(__name__)
_XBEE_LOGGER = logging.getLogger("xbee_humidifier")

ATTR_SAVED_HUMIDITY = "saved_humidity"
ATTR_DATA = "data"

XBEE_DATA_CLUSTER = 0x11
SERIAL_DATA_CMD = 0x0000
XBEE_DATA_ENDPOINT = 0xE8

REMOTE_COMMAND_TIMEOUT = 30


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the humidifier platform."""
    humidifiers = []
    coordinator = hass.data[DOMAIN][entry.entry_id]
    for number in range(0, 3):
        config = entry.data["humidifier_" + str(number)]
        name = config[CONF_NAME]
        sensor_entity_id = config[CONF_SENSOR]
        target_humidity = config.get(CONF_TARGET_HUMIDITY)
        away_humidity = config.get(CONF_AWAY_HUMIDITY)
        entity_description = HumidifierEntityDescription(
            key="xbee_humidifier_" + str(number),
            name="Integration Humidifier " + str(number),
            icon="mdi:humidifier",
            device_class=HumidifierDeviceClass.HUMIDIFIER,
        )
        humidifiers.append(
            XBeeHumidifier(
                name,
                number,
                sensor_entity_id,
                target_humidity,
                away_humidity,
                entity_description,
                coordinator,
            )
        )

    async_add_entities(humidifiers)


class XBeeHumidifier(XBeeHumidifierEntity, HumidifierEntity, RestoreEntity):
    """Representation of an XBee Humidifier device."""

    def __init__(
        self,
        name,
        number,
        sensor_entity_id,
        target_humidity,
        away_humidity,
        entity_description,
        coordinator,
    ):
        """Initialize the hygrostat."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._name = name
        self._number = number
        self._sensor_entity_id = sensor_entity_id
        self._saved_target_humidity = away_humidity or target_humidity
        self._active = False
        self._target_humidity = target_humidity
        self._attr_supported_features = 0
        if away_humidity:
            self._attr_supported_features |= HumidifierEntityFeature.MODES
        self._away_humidity = away_humidity
        self._is_away = False
        self._state = None
        self._min_humidity = None
        self._max_humidity = None
        self._remove_sensor_tracking = None
        self._attr_unique_id = coordinator.config_entry.entry_id + str(self._number)

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        if (old_state := await self.async_get_last_state()) is not None:
            if old_state.attributes.get(ATTR_MODE) == MODE_AWAY:
                self._is_away = True
                self._saved_target_humidity = self._target_humidity
                self._target_humidity = self._away_humidity or self._target_humidity
            if old_state.attributes.get(ATTR_HUMIDITY):
                self._target_humidity = int(old_state.attributes[ATTR_HUMIDITY])
            if old_state.attributes.get(ATTR_SAVED_HUMIDITY):
                self._saved_target_humidity = int(
                    old_state.attributes[ATTR_SAVED_HUMIDITY]
                )
            if old_state.state:
                self._state = old_state.state == STATE_ON
        if self._state is None:
            self._state = False

        self._remove_zha_tracking = None

        @callback
        async def async_zha_loaded(event):
            if self._remove_zha_tracking is not None:
                self._remove_zha_tracking()
                self._remove_zha_tracking = None
            await self._async_startup(None)

        @callback
        def zha_filter(event):
            return event.data["component"] == "zha"

        self.hass.bus.async_listen(EVENT_COMPONENT_LOADED, async_zha_loaded, zha_filter)

        await self._async_startup(None)  # init the sensor

        async def async_log(data):
            if data["msg"] in ("Not initialized", "Main loop started"):
                await self._async_startup(None)

        self.async_on_remove(self.coordinator.client.add_subscriber("log", async_log))

        async def async_update_available(value):
            self._active = value
            await self.async_update_ha_state()
            if not value:
                await self._async_startup(None)

        self.async_on_remove(
            self.coordinator.client.add_subscriber(
                "available_" + str(self._number), async_update_available
            )
        )

    @callback
    async def _async_startup(self, _now):
        """Init on startup."""
        resp = await self.coordinator.client.command("hum", self._number)

        self._min_humidity = resp["cap_attr"]["min_hum"]
        self._max_humidity = resp["cap_attr"]["max_hum"]

        if resp["cur_hum"] is not None:
            self._state = resp["is_on"]
            self._is_away = resp["state_attr"]["mode"] == "away"
            self._target_humidity = resp["state_attr"]["hum"]
            self._saved_target_humidity = resp["extra_state_attr"]["sav_hum"]
            self._active = resp["available"]
        elif self._target_humidity is not None:
            if self._is_away:
                await self.coordinator.client.command(
                    "hum", self._number, mode=MODE_NORMAL
                )
                await self.coordinator.client.command(
                    "hum", self._number, hum=self._saved_target_humidity
                )
                await self.coordinator.client.command(
                    "hum", self._number, mode=MODE_AWAY
                )
                await self.coordinator.client.command(
                    "hum", self._number, hum=self._target_humidity
                )
            elif self._saved_target_humidity is not None:
                await self.coordinator.client.command(
                    "hum", self._number, mode=MODE_AWAY
                )
                await self.coordinator.client.command(
                    "hum", self._number, hum=self._saved_target_humidity
                )
                await self.coordinator.client.command(
                    "hum", self._number, mode=MODE_NORMAL
                )
                await self.coordinator.client.command(
                    "hum", self._number, hum=self._target_humidity
                )
            else:
                await self.coordinator.client.command(
                    "hum", self._number, mode=MODE_NORMAL
                )
                await self.coordinator.client.command(
                    "hum", self._number, hum=self._target_humidity
                )
            await self.coordinator.client.command(
                "hum", self._number, is_on=self._state
            )

        sensor_state = self.hass.states.get(self._sensor_entity_id)
        if sensor_state is not None and sensor_state.state not in (
            STATE_UNKNOWN,
            STATE_UNAVAILABLE,
        ):
            await self._async_sensor_changed(self._sensor_entity_id, None, sensor_state)

        # Add listener
        if self._remove_sensor_tracking is None:
            self._remove_sensor_tracking = async_track_state_change(
                self.hass, self._sensor_entity_id, self._async_sensor_changed
            )
            self.async_on_remove(self._remove_sensor_tracking)

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
        return HumidifierDeviceClass.HUMIDIFIER

    async def async_turn_on(self, **kwargs):
        """Turn hygrostat on."""
        if (
            await self.coordinator.client.command("hum", self._number, is_on=True)
            == "OK"
        ):
            self._state = True
        await self.async_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn hygrostat off."""
        if (
            await self.coordinator.client.command("hum", self._number, is_on=False)
            == "OK"
        ):
            self._state = False
        await self.async_update_ha_state()

    async def async_set_humidity(self, humidity: int):
        """Set new target humidity."""
        if humidity is None:
            return
        if (
            await self.coordinator.client.command("hum", self._number, hum=humidity)
            == "OK"
        ):
            self._target_humidity = humidity
        await self.async_update_ha_state()

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
            return

        await self.coordinator.client.command(
            "hum", self._number, cur_hum=new_state.state
        )
        await self.async_update_ha_state()

    async def async_set_mode(self, mode: str):
        """Set new mode."""
        if self._away_humidity is None:
            return

        if (
            await self.coordinator.client.command("hum", self._number, mode=mode)
            == "OK"
        ):
            if self._is_away != mode == MODE_AWAY:
                self._target_humidity, self._saved_target_humidity = (
                    self._saved_target_humidity,
                    self._target_humidity,
                )
            self._is_away = mode == MODE_AWAY
        await self.async_update_ha_state()
