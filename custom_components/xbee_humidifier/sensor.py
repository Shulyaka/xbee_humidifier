"""xbee_humidifier sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import XBeeHumidifierDataUpdateCoordinator
from .entity import XBeeHumidifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the sensor platform."""
    sensors = []
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entity_description = SensorEntityDescription(
        key="xbee_humidifier_pump_temperature",
        name="Pump Temperature",
        has_entity_name=True,
        icon="mdi:hydraulic-oil-temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="°C",
        state_class=SensorStateClass.MEASUREMENT,
    )
    sensors.append(
        XBeeHumidifierSensor(
            name="pump_temp",
            coordinator=coordinator,
            entity_description=entity_description,
        )
    )

    entity_description = SensorEntityDescription(
        key="xbee_humidifier_pressure_in",
        name="Pressure In",
        has_entity_name=True,
        icon="mdi:gauge-low",
        device_class=SensorDeviceClass.PRESSURE,
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement="bar",
        state_class=SensorStateClass.MEASUREMENT,
    )
    sensors.append(
        XBeeHumidifierSensor(
            name="pressure_in",
            coordinator=coordinator,
            entity_description=entity_description,
            conversion=lambda x: (x / 4096 * 3.3 * 8 - 4) / 3,
        )
    )

    async_add_entities(sensors)


class XBeeHumidifierSensor(XBeeHumidifierEntity, SensorEntity):
    """Representation of an XBee Humidifier sensors."""

    def __init__(
        self,
        name,
        coordinator: XBeeHumidifierDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
        conversion=None,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._name = name
        self._attr_unique_id = coordinator.unique_id + name
        self._conversion = conversion

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        self._handle_coordinator_update()

        async def async_update_state(value):
            if self._conversion is not None:
                value = self._conversion(value)
            self._attr_native_value = value
            self.async_write_ha_state()

        self.async_on_remove(
            self.coordinator.client.add_subscriber(self._name, async_update_state)
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        value = self.coordinator.data.get(self._name)
        if self._conversion is not None:
            value = self._conversion(value)
        self._attr_native_value = value

        self.async_write_ha_state()
