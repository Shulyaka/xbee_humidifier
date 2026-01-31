"""Adds config flow for xbee_humidifier."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import callback
from homeassistant.helpers import selector

from . import (
    CONF_AWAY_HUMIDITY,
    CONF_DEVICE_IEEE,
    CONF_MAX_HUMIDITY,
    CONF_MIN_HUMIDITY,
    CONF_SENSOR,
    CONF_TARGET_HUMIDITY,
)
from .const import DOMAIN
from .coordinator import XBeeHumidifierApiClient

DEFAULT_NAME = "XBee Humidifier"

XBEE_HUMIDIFIER_SCHEMA = {
    vol.Optional(CONF_SENSOR): selector.EntitySelector(
        selector.EntitySelectorConfig(domain=SENSOR_DOMAIN)
    ),
    vol.Optional(CONF_TARGET_HUMIDITY): selector.NumberSelector(
        selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
    ),
    vol.Optional(CONF_AWAY_HUMIDITY): selector.NumberSelector(
        selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
    ),
    vol.Optional(CONF_MIN_HUMIDITY): selector.NumberSelector(
        selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
    ),
    vol.Optional(CONF_MAX_HUMIDITY): selector.NumberSelector(
        selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
    ),
}


class XBeeHumidifierFlowHandler:
    """Common class for config and options flows."""

    async def async_step_humidifier(
        self,
        number,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier configuration."""
        _errors = {}
        if user_input is not None:
            self.humidifier[number] = user_input
            if number < 2:
                return await getattr(self, "async_step_humidifier_" + str(number + 1))()

            return self._async_create_entry(
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
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 0 configuration."""
        return await self.async_step_humidifier(0, user_input)

    async def async_step_humidifier_1(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 1 configuration."""
        return await self.async_step_humidifier(1, user_input)

    async def async_step_humidifier_2(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Handle humidifier 2 configuration."""
        return await self.async_step_humidifier(2, user_input)


class XBeeHumidifierOptionsFlowHandler(
    XBeeHumidifierFlowHandler, config_entries.OptionsFlow
):
    """Options flow for XBee Humidifier."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""

        self.device_ieee = self.config_entry.data[CONF_DEVICE_IEEE]
        self.humidifier = {}

        self.hum = {}
        for number in range(0, 3):
            self.hum[number] = {
                CONF_SENSOR: self.config_entry.options.get(
                    "humidifier_" + str(number), {}
                ).get(CONF_SENSOR),
                CONF_TARGET_HUMIDITY: self.config_entry.options.get(
                    "humidifier_" + str(number), {}
                ).get(CONF_TARGET_HUMIDITY),
                CONF_AWAY_HUMIDITY: self.config_entry.options.get(
                    "humidifier_" + str(number), {}
                ).get(CONF_AWAY_HUMIDITY),
                CONF_MIN_HUMIDITY: self.config_entry.options.get(
                    "humidifier_" + str(number), {}
                ).get(CONF_MIN_HUMIDITY),
                CONF_MAX_HUMIDITY: self.config_entry.options.get(
                    "humidifier_" + str(number), {}
                ).get(CONF_MAX_HUMIDITY),
            }

        return await self.async_step_humidifier_0(user_input=user_input)

    def _async_create_entry(
        self, title: str, data: dict[str, Any], options: dict[str, Any]
    ):
        """Return result entry for option flow."""
        return self.async_create_entry(title=title, data=options)


class XBeeHumidifierConfigFlowHandler(
    XBeeHumidifierFlowHandler, config_entries.ConfigFlow, domain=DOMAIN
):
    """Config flow for XBee Humidifier."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return XBeeHumidifierOptionsFlowHandler()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
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
                    self.hum[number] = {
                        CONF_TARGET_HUMIDITY: await client.async_command(
                            "target_hum", number
                        ),
                        CONF_AWAY_HUMIDITY: await client.async_command(
                            "sav_hum", number
                        ),
                        CONF_MIN_HUMIDITY: 15,
                        CONF_MAX_HUMIDITY: 100,
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

    def _async_create_entry(
        self, title: str, data: dict[str, Any], options: dict[str, Any]
    ) -> config_entries.FlowResult:
        """Return result entry for config flow."""
        return self.async_create_entry(title=title, data=data, options=options)
