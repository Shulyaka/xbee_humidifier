"""XBeeHumidifierEntity class."""
from __future__ import annotations

from homeassistant.components.zha import DOMAIN as ZHA_DOMAIN
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, NAME
from .coordinator import XBeeHumidifierDataUpdateCoordinator


class XBeeHumidifierEntity(CoordinatorEntity):
    """XBeeHumidifierEntity class."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self, coordinator: XBeeHumidifierDataUpdateCoordinator, number=None
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        sw_version = (
            "Version: "
            + coordinator.version_info["VR"]
            + ", Build: "
            + coordinator.version_info["Build"]
            + ", Bootloader: "
            + coordinator.version_info["VH"]
            + ", Compiler: "
            + coordinator.version_info["Compiler"]
            + ", Stack: "
            + coordinator.version_info["Stack"]
        )

        if number is not None:
            self._attr_device_info = DeviceInfo(
                identifiers={
                    (DOMAIN, coordinator.client.device_ieee + "-" + str(number))
                },
                name=NAME + " " + str(number + 1),
                model=coordinator.version_info["Model"],
                manufacturer=ATTRIBUTION,
                via_device=(DOMAIN, coordinator.client.device_ieee),
                hw_version=coordinator.version_info["HV"],
                sw_version=sw_version,
            )
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.client.device_ieee)},
                name=NAME + " Main Unit",
                model=coordinator.version_info["Model"],
                manufacturer=ATTRIBUTION,
                via_device=(ZHA_DOMAIN, coordinator.client.device_ieee),
                hw_version=coordinator.version_info["HV"],
                sw_version=sw_version,
            )
