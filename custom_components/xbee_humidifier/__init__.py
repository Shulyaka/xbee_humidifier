"""The xbee_humidifier custom component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import XBeeHumidifierDataUpdateCoordinator

CONF_SENSOR = "target_sensor"
CONF_TARGET_HUMIDITY = "target_humidity"
CONF_AWAY_HUMIDITY = "away_humidity"
CONF_NUMBER = "number"
CONF_DEVICE_IEEE = "device_ieee"


PLATFORMS: list[Platform] = [
    Platform.HUMIDIFIER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][
        entry.entry_id
    ] = coordinator = XBeeHumidifierDataUpdateCoordinator(
        hass=hass,
        device_ieee=entry.data[CONF_DEVICE_IEEE],
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
