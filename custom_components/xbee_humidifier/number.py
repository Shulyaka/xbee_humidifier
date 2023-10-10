"""xbee_humidifier pump speed controls."""
from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.components.number.const import NumberMode
from homeassistant.const import EntityCategory

from .const import DOMAIN
from .coordinator import XBeeHumidifierDataUpdateCoordinator
from .entity import XBeeHumidifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform."""
    numbers = []
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entity_description = NumberEntityDescription(
        key="xbee_humidifier_pump_speed",
        name="Pump Speed",
        has_entity_name=True,
        icon="hass:speedometer",
        native_min_value=0,
        native_max_value=1023,
        native_step=1,
        native_unit_of_measurement="rpm",
        device_class=NumberDeviceClass.SPEED,
        entity_category=EntityCategory.CONFIG,
    )
    numbers.append(
        XBeeHumidifierNumber(
            name="pump_speed",
            coordinator=coordinator,
            entity_description=entity_description,
        )
    )

    async_add_entities(numbers)


class XBeeHumidifierNumber(XBeeHumidifierEntity, NumberEntity):
    """Representation of an XBee Humidifier input numbers."""

    def __init__(
        self,
        name,
        coordinator: XBeeHumidifierDataUpdateCoordinator,
        entity_description: NumberEntityDescription,
    ) -> None:
        """Initialize the number class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._name = name
        self._state = None
        self._attr_mode = NumberMode.SLIDER
        self._attr_unique_id = coordinator.unique_id + name

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        try:
            self._state = await self.coordinator.client.async_command(self._name)
        except TimeoutError:
            pass

        async def async_update_state(value):
            self._state = value
            self.async_schedule_update_ha_state()

        self.async_on_remove(
            self.coordinator.client.add_subscriber(self._name, async_update_state)
        )

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        return self._state

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        value = int(value)
        resp = await self.coordinator.client.async_command(self._name, value)
        if resp == "OK":
            self._state = value
            self.async_schedule_update_ha_state()
