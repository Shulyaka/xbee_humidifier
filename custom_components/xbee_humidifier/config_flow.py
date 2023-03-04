"""Adds config flow for xbee_humidifier."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from . import (
    CONF_AWAY_HUMIDITY,
    CONF_DEVICE_IEEE,
    CONF_NUMBER,
    CONF_SENSOR,
    CONF_TARGET_HUMIDITY,
    DOMAIN,
)

DEFAULT_NAME = "XBee Humidifier"

XBEE_HUMIDIFIER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUMBER): vol.In([0, 1, 2]),
        vol.Required(CONF_SENSOR): cv.entity_id,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_TARGET_HUMIDITY): vol.Coerce(int),
        vol.Optional(CONF_AWAY_HUMIDITY): vol.Coerce(int),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_IEEE): cv.string,
        vol.Required(1): XBEE_HUMIDIFIER_SCHEMA,
        vol.Required(2): XBEE_HUMIDIFIER_SCHEMA,
        vol.Required(3): XBEE_HUMIDIFIER_SCHEMA,
    }
)


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
            return self.async_create_entry(
                title=user_input[CONF_DEVICE_IEEE],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=_errors,
        )
