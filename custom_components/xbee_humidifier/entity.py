"""XBeeHumidifierEntity class."""

from __future__ import annotations

from homeassistant.helpers.entity import ChildDeviceInfo, DeviceInfo
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

        if number is not None:
            self._attr_device_info = ChildDeviceInfo(
                identifiers={
                    (DOMAIN, coordinator.client.device_ieee + "-" + str(number))
                },
                name=NAME + " " + str(number + 1),
                parent_device_id=coordinator.device_id,
            )
        else:
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
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.client.device_ieee)},
                name=NAME + " Main Unit",
                model=coordinator.version_info["Model"],
                manufacturer=ATTRIBUTION,
                via_device_id=coordinator.zha_device_id,
                hw_version=coordinator.version_info["HV"],
                sw_version=sw_version,
            )
