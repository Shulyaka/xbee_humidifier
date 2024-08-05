"""xbee_humidifier valves."""
from __future__ import annotations

from homeassistant.components.valve import (
    ValveDeviceClass,
    ValveEntity,
    ValveEntityDescription,
    ValveEntityFeature,
)
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import XBeeHumidifierDataUpdateCoordinator
from .entity import XBeeHumidifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform."""
    valves = []
    coordinator = hass.data[DOMAIN][entry.entry_id]
    for number in range(0, 4):
        entity_description = ValveEntityDescription(
            key="xbee_humidifier_valve_" + str(number + 1),
            name="Valve" if number != 3 else "Pressure Drop Valve",
            has_entity_name=True,
            icon="mdi:pipe-valve",
            device_class=ValveDeviceClass.WATER,
            entity_category=EntityCategory.DIAGNOSTIC,
            reports_position=False,
        )
        valves.append(
            XBeeHumidifierValve(
                name="valve",
                number=number,
                coordinator=coordinator,
                entity_description=entity_description,
            )
        )

    async_add_entities(valves)


class XBeeHumidifierValve(XBeeHumidifierEntity, ValveEntity):
    """Representation of an XBee Humidifier valves."""

    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    def __init__(
        self,
        name,
        number,
        coordinator: XBeeHumidifierDataUpdateCoordinator,
        entity_description: ValveEntityDescription,
    ) -> None:
        """Initialize the valve class."""
        self.entity_description = entity_description
        self._attr_unique_id = coordinator.unique_id + (
            name if number is None else name + str(number)
        )
        super().__init__(coordinator, number if number != 3 else None)
        self._name = name
        self._number = number

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        self._handle_coordinator_update()

        async def async_update_state(value):
            self._attr_is_closed = not value
            self.async_write_ha_state()

        subscriber_name = (
            self._name if self._number is None else self._name + "_" + str(self._number)
        )
        self.async_on_remove(
            self.coordinator.client.add_subscriber(subscriber_name, async_update_state)
        )

    async def _turn(self, is_on: bool) -> None:
        """Turn on or off the valve."""
        if self._number is None:
            resp = await self.coordinator.client.async_command(self._name, is_on)
        else:
            resp = await self.coordinator.client.async_command(
                self._name, self._number, is_on
            )

        if resp == "OK":
            self._attr_is_closed = not is_on
            self.async_write_ha_state()

    async def async_open_valve(self, **_: any) -> None:
        """Open valve."""
        await self._turn(True)

    async def async_close_valve(self, **_: any) -> None:
        """Close the valve."""
        await self._turn(False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data.get(self._name)
        if data is not None and self._number is not None:
            data = data.get(self._number)
        self._attr_is_closed = not data

        self.schedule_update_ha_state()
