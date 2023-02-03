"""The xbee_humidifier custom component."""
from homeassistant.const import CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, discovery
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

DOMAIN = "xbee_humidifier"

CONF_SENSOR = "target_sensor"
CONF_TARGET_HUMIDITY = "target_humidity"
CONF_AWAY_HUMIDITY = "away_humidity"
CONF_NUMBER = "number"
CONF_DEVICE_IEEE = "device_ieee"

DEFAULT_NAME = "XBee Humidifier"

XBEE_HUMIDIFIER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NUMBER): vol.In([0, 1, 2]),
        vol.Required(CONF_SENSOR): cv.entity_id,
        vol.Required(CONF_DEVICE_IEEE): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_TARGET_HUMIDITY): vol.Coerce(int),
        vol.Optional(CONF_AWAY_HUMIDITY): vol.Coerce(int),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [XBEE_HUMIDIFIER_SCHEMA])},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Generic Hygrostat component."""
    if DOMAIN not in config:
        return True

    for humidifier_conf in config[DOMAIN]:
        hass.async_create_task(
            discovery.async_load_platform(
                hass, Platform.HUMIDIFIER, DOMAIN, humidifier_conf, config
            )
        )

    return True
