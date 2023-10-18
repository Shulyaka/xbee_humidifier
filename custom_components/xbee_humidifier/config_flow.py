"""Adds config flow for xbee_humidifier."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.helpers import selector

from . import CONF_AWAY_HUMIDITY, CONF_DEVICE_IEEE, CONF_SENSOR, CONF_TARGET_HUMIDITY
from .const import DOMAIN
from .coordinator import XBeeHumidifierApiClient

DEFAULT_NAME = "XBee Humidifier"

XBEE_HUMIDIFIER_SCHEMA = {
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
                    self.hum[number] = {
                        CONF_TARGET_HUMIDITY: hum["state_attr"]["hum"],
                        CONF_AWAY_HUMIDITY: hum["extra_state_attr"].get("sav_hum"),
                    }
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

    async def async_step_humidifier(
        self,
        number,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier configuration."""
        _errors = {}
        if user_input is not None:
            self.humidifier[number] = user_input
            if number < 2:
                return await getattr(self, "async_step_humidifier_" + str(number + 1))()

            return self.async_create_entry(
                title=self.device_ieee,
                data={
                    CONF_DEVICE_IEEE: self.device_ieee,
                },
                options={
                    "humidifier_0": self.humidifier[0],
                    "humidifier_1": self.humidifier[1],
                    "humidifier_2": self.humidifier[2],
                },
            )

        return self.async_show_form(
            step_id="humidifier_" + str(number),
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(XBEE_HUMIDIFIER_SCHEMA),
                self.hum[number],
            ),
            errors=_errors,
        )

    async def async_step_humidifier_0(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 0 configuration."""
        return await self.async_step_humidifier(0, user_input)

    async def async_step_humidifier_1(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 1 configuration."""
        return await self.async_step_humidifier(1, user_input)

    async def async_step_humidifier_2(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 2 configuration."""
        return await self.async_step_humidifier(2, user_input)
