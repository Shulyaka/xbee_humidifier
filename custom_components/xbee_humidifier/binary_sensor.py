"""xbee_humidifier binary sensor."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

from .const import DOMAIN
from .coordinator import XBeeHumidifierDataUpdateCoordinator
from .entity import XBeeHumidifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the humidifier platform."""
    binary_sensors = []
    coordinator = hass.data[DOMAIN][entry.entry_id]
    for number in range(0, 3):
        entity_description = BinarySensorEntityDescription(
            key="xbee_humidifier_working_" + str(number + 1),
            name="Working " + str(number + 1),
            device_class=BinarySensorDeviceClass.RUNNING,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        binary_sensors.append(
            XBeeHumidifierWorkingSensor(
                number,
                coordinator=coordinator,
                entity_description=entity_description,
            )
        )

    async_add_entities(binary_sensors)


class XBeeHumidifierWorkingSensor(XBeeHumidifierEntity, BinarySensorEntity):
    """Representation of an XBee Humidifier working binary sensor."""

    def __init__(
        self,
        number,
        coordinator: XBeeHumidifierDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._number = number
        self._state = None
        self._attr_unique_id = coordinator.unique_id + "working" + str(self._number)

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        self._state = self.coordinator.data.get(self._number, {}).get("working")

        async def async_update_state(value):
            self._state = value
            await self.async_update_ha_state()

        self.async_on_remove(
            self.coordinator.client.add_subscriber(
                "working_" + str(self._number), async_update_state
            )
        )

    @property
    def is_on(self) -> bool:
        """Return true if the hygrostat is currently working."""
        return self._state
