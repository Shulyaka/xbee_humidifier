"""XBeeHumidifierEntity class."""
from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME, VERSION
from .coordinator import XBeeHumidifierDataUpdateCoordinator


class XBeeHumidifierEntity(CoordinatorEntity):
    """XBeeHumidifierEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: XBeeHumidifierDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=NAME,
            model=VERSION,
            manufacturer=NAME,
        )
