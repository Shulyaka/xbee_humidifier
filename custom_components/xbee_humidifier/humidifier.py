"""Adds support for xbee_humidifier units."""
from __future__ import annotations

import asyncio
import json
import logging

from homeassistant.components.humidifier import (
    ATTR_HUMIDITY,
    MODE_AWAY,
    MODE_NORMAL,
    PLATFORM_SCHEMA,
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.components.zha import DOMAIN as ZHA_DOMAIN
from homeassistant.components.zha.api import SERVICE_ISSUE_ZIGBEE_CLUSTER_COMMAND
from homeassistant.components.zha.core.const import (
    ATTR_CLUSTER_ID,
    ATTR_CLUSTER_TYPE,
    ATTR_COMMAND_TYPE,
    ATTR_ENDPOINT_ID,
    ATTR_IEEE,
    ATTR_PARAMS,
    CLUSTER_COMMAND_SERVER,
    CLUSTER_TYPE_IN,
    ZHA_EVENT,
)
from homeassistant.const import ATTR_COMMAND, ATTR_MODE, CONF_NAME, STATE_ON
from homeassistant.core import DOMAIN as HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later, async_track_state_change
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import (
    CONF_AWAY_HUMIDITY,
    CONF_DEVICE_IEEE,
    CONF_NUMBER,
    CONF_SENSOR,
    CONF_TARGET_HUMIDITY,
    XBEE_HUMIDIFIER_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)
_XBEE_LOGGER = logging.getLogger("xbee_humidifier")

ATTR_SAVED_HUMIDITY = "saved_humidity"
ATTR_DATA = "data"

XBEE_DATA_CLUSTER = 0x11
SERIAL_DATA_CMD = 0x0000
XBEE_DATA_ENDPOINT = 0xE8

REMOTE_COMMAND_TIMEOUT = 30

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(XBEE_HUMIDIFIER_SCHEMA.schema)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the generic hygrostat platform."""
    if discovery_info:
        config = discovery_info
    name = config[CONF_NAME]
    device_ieee = config[CONF_DEVICE_IEEE]
    number = config[CONF_NUMBER]
    sensor_entity_id = config[CONF_SENSOR]
    target_humidity = config.get(CONF_TARGET_HUMIDITY)
    away_humidity = config.get(CONF_AWAY_HUMIDITY)

    async_add_entities(
        [
            XBeeHumidifier(
                name,
                device_ieee,
                number,
                sensor_entity_id,
                target_humidity,
                away_humidity,
            )
        ]
    )


class XBeeHumidifier(HumidifierEntity, RestoreEntity):
    """Representation of a Generic Hygrostat device."""

    _attr_should_poll = False

    _cmd_lock = {}
    _cmd_resp_lock = asyncio.Lock()
    _log_handler = None

    def __init__(
        self,
        name,
        device_ieee,
        number,
        sensor_entity_id,
        target_humidity,
        away_humidity,
    ):
        """Initialize the hygrostat."""
        self._name = name
        self._device_ieee = device_ieee
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
        self._awaiting = {}
        self._state = None
        self._min_humidity = None
        self._max_humidity = None
        if XBeeHumidifier._log_handler is None:
            XBeeHumidifier._log_handler = self._number

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        async def async_zha_event(event):
            await self._async_data_received(event.data["args"]["data"])

        @callback
        def ieee_event_filter(event):
            return (
                event.data["command"] == "receive_data"
                and event.data["device_ieee"] == self._device_ieee
            )

        self.hass.bus.async_listen(ZHA_EVENT, async_zha_event, ieee_event_filter)

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

        await self._async_startup(None)  # init the sensor

    @callback
    async def _async_startup(self, _now):
        """Init on startup."""
        try:
            resp = await self._command("bind")
            if resp != "OK":
                _LOGGER.error("Bind response: %s", resp)
                raise RuntimeError("Could not bind")
        except Exception as e:
            _LOGGER.error(type(e).__name__ + ": " + str(e))
            _LOGGER.debug("Will retry after 30 sec")
            async_call_later(self.hass, 30, self._async_startup)
            return

        resp = await self._command("hum", self._number)

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
                await self._command("hum", self._number, mode=MODE_NORMAL)
                await self._command(
                    "hum", self._number, hum=self._saved_target_humidity
                )
                await self._command("hum", self._number, mode=MODE_AWAY)
                await self._command("hum", self._number, hum=self._target_humidity)
            elif self._saved_target_humidity is not None:
                await self._command("hum", self._number, mode=MODE_AWAY)
                await self._command(
                    "hum", self._number, hum=self._saved_target_humidity
                )
                await self._command("hum", self._number, mode=MODE_NORMAL)
                await self._command("hum", self._number, hum=self._target_humidity)
            else:
                await self._command("hum", self._number, mode=MODE_NORMAL)
                await self._command("hum", self._number, hum=self._target_humidity)
            await self._command("hum", self._number, is_on=self._state)

        sensor_state = self.hass.states.get(self._sensor_entity_id)
        await self._async_sensor_changed(self._sensor_entity_id, None, sensor_state)

        # Add listener
        async_track_state_change(
            self.hass, self._sensor_entity_id, self._async_sensor_changed
        )

    async def _command(self, command, *args, **kwargs):
        if len(args) > 0 and len(kwargs) > 0:
            data = {"cmd": command, "args": (args, kwargs)}
        elif len(args) > 1:
            data = {"cmd": command, "args": args}
        elif len(args) == 1:
            data = {"cmd": command, "args": args[0]}
        elif len(kwargs) > 0:
            data = {"cmd": command, "args": kwargs}
        else:
            data = {"cmd": command}

        data = json.dumps(data)

        _LOGGER.debug("data: %s", data)

        if command not in XBeeHumidifier._cmd_lock:
            XBeeHumidifier._cmd_lock[command] = asyncio.Lock()

        async with XBeeHumidifier._cmd_lock[command]:
            try:
                return await asyncio.wait_for(
                    await self._cmd(command, data),
                    timeout=REMOTE_COMMAND_TIMEOUT,
                )
            except asyncio.TimeoutError:
                _LOGGER.warning("No response to %s command", command)
                del self._awaiting[command]
                raise

    async def _cmd(self, command, data):
        if command in self._awaiting:
            raise RuntimeError("Command is already executing")

        data = {
            ATTR_CLUSTER_ID: XBEE_DATA_CLUSTER,
            ATTR_CLUSTER_TYPE: CLUSTER_TYPE_IN,
            ATTR_COMMAND: SERIAL_DATA_CMD,
            ATTR_COMMAND_TYPE: CLUSTER_COMMAND_SERVER,
            ATTR_ENDPOINT_ID: XBEE_DATA_ENDPOINT,
            ATTR_IEEE: self._device_ieee,
            ATTR_PARAMS: {ATTR_DATA: data},
        }

        future = asyncio.Future()

        self._awaiting[command] = future

        try:
            await self.hass.services.async_call(
                ZHA_DOMAIN, SERVICE_ISSUE_ZIGBEE_CLUSTER_COMMAND, data
            )
        except Exception as e:
            future.set_exception(e)
            del self._awaiting[command]

        return future

    async def _async_data_received(self, data):
        data = json.loads(data)
        for key, value in data.items():
            if key[-5:] == "_resp":
                async with XBeeHumidifier._cmd_resp_lock:
                    command = key[:-5]
                    if command not in self._awaiting:
                        continue
                    future = self._awaiting.pop(command)
                    if isinstance(value, dict) and "err" in value:
                        future.set_exception(
                            RuntimeError("Command response: {}".format(value["err"]))
                        )
                        continue
                    _LOGGER.debug("%s response: %s", command, value)
                    future.set_result(value)
            elif key == "log":
                if XBeeHumidifier._log_handler == self._number:
                    _XBEE_LOGGER.log(value["sev"], value["msg"])
            elif key == "pump":
                _LOGGER.debug("pump = %s", value)
            elif key == "pump_temp":
                _LOGGER.debug("pump_temp = %s", value)
            elif key[:6] == "valve_":
                _LOGGER.debug("%s = %s", key, value)
            elif key[:10] == "available_":
                _LOGGER.debug("%s = %s", key, value)
                if int(key[10:]) == self._number:
                    self._active = value
                    await self.async_update_ha_state()
            elif key[:8] == "working_":
                _LOGGER.debug("%s = %s", key, value)
            else:
                _LOGGER.debug("Unhandled message received: %s", {key: value})

    @property
    def available(self):
        """Return True if entity is available."""
        return self._active

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
        if await self._command("hum", self._number, is_on=True) == "OK":
            self._state = True
        await self.async_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn hygrostat off."""
        if await self._command("hum", self._number, is_on=False) == "OK":
            self._state = False
        await self.async_update_ha_state()

    async def async_set_humidity(self, humidity: int):
        """Set new target humidity."""
        if humidity is None:
            return
        if await self._command("hum", self._number, hum=humidity) == "OK":
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

        await self._command("hum", self._number, cur_hum=new_state.state)
        await self.async_update_ha_state()

    async def async_set_mode(self, mode: str):
        """Set new mode."""
        if self._away_humidity is None:
            return

        if await self._command("hum", self._number, mode=mode) == "OK":
            if self._is_away != mode == MODE_AWAY:
                self._target_humidity, self._saved_target_humidity = (
                    self._saved_target_humidity,
                    self._target_humidity,
                )
            self._is_away = mode == MODE_AWAY
        await self.async_update_ha_state()
