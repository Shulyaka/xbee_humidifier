"""Adds config flow for xbee_humidifier."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
import voluptuous as vol

from . import CONF_AWAY_HUMIDITY, CONF_DEVICE_IEEE, CONF_SENSOR, CONF_TARGET_HUMIDITY
from .const import DOMAIN
from .coordinator import XBeeHumidifierApiClient

DEFAULT_NAME = "XBee Humidifier"

XBEE_HUMIDIFIER_SCHEMA = {
    vol.Optional(CONF_NAME): str,
    vol.Required(CONF_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(domain=SENSOR_DOMAIN)
    ),
    vol.Optional(CONF_TARGET_HUMIDITY): selector.NumberSelector(
        selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
    ),
    vol.Optional(CONF_AWAY_HUMIDITY): selector.NumberSelector(
        selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
    ),
}


class XBeeHumidifierFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for XBee Humidifier."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                client = XBeeHumidifierApiClient(
                    self.hass, user_input[CONF_DEVICE_IEEE]
                )
                unique_id = await client.async_command("unique_id")
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                self.hum = {}
                for number in range(0, 3):
                    hum = await client.async_command("hum", number)
                    target_humidity = hum["state_attr"]["hum"]
                    away_humidity = hum["extra_state_attr"].get("sav_hum")
                    self.hum[number] = (target_humidity, away_humidity)
                client.stop()
            except Exception as err:
                _errors["base"] = str(err)
                client.stop()
            else:
                self.device_ieee = user_input[CONF_DEVICE_IEEE]
                self.humidifier = {}
                return await self.async_step_humidifier_0()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE_IEEE): str}),
            errors=_errors,
        )

    async def async_step_humidifier_0(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 0 configuration."""
        _errors = {}
        if user_input is not None:
            self.humidifier[0] = user_input
            return await self.async_step_humidifier_1()

        target_humidity, away_humidity = self.hum[0]

        return self.async_show_form(
            step_id="humidifier_0",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(XBEE_HUMIDIFIER_SCHEMA),
                {
                    CONF_NAME: DEFAULT_NAME + " 1",
                    CONF_TARGET_HUMIDITY: target_humidity,
                    CONF_AWAY_HUMIDITY: away_humidity,
                },
            ),
            errors=_errors,
        )

    async def async_step_humidifier_1(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 1 configuration."""
        _errors = {}
        if user_input is not None:
            self.humidifier[1] = user_input
            return await self.async_step_humidifier_2()

        target_humidity, away_humidity = self.hum[1]

        return self.async_show_form(
            step_id="humidifier_1",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(XBEE_HUMIDIFIER_SCHEMA),
                {
                    CONF_NAME: DEFAULT_NAME + " 2",
                    CONF_TARGET_HUMIDITY: target_humidity,
                    CONF_AWAY_HUMIDITY: away_humidity,
                },
            ),
            errors=_errors,
        )

    async def async_step_humidifier_2(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 2 configuration."""
        _errors = {}
        if user_input is not None:
            self.humidifier[2] = user_input
            return self.async_create_entry(
                title=self.device_ieee,
                data={
                    CONF_DEVICE_IEEE: self.device_ieee,
                    "humidifier_0": self.humidifier[0],
                    "humidifier_1": self.humidifier[1],
                    "humidifier_2": self.humidifier[2],
                },
            )

        target_humidity, away_humidity = self.hum[2]

        return self.async_show_form(
            step_id="humidifier_2",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(XBEE_HUMIDIFIER_SCHEMA),
                {
                    CONF_NAME: DEFAULT_NAME + " 3",
                    CONF_TARGET_HUMIDITY: target_humidity,
                    CONF_AWAY_HUMIDITY: away_humidity,
                },
            ),
            errors=_errors,
        )
