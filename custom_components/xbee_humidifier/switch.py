"""xbee_humidifier valves and pump controls."""
from __future__ import annotations

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .const import DOMAIN
from .coordinator import XBeeHumidifierDataUpdateCoordinator
from .entity import XBeeHumidifierEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform."""
    switches = []
    coordinator = hass.data[DOMAIN][entry.entry_id]
    for number in range(0, 4):
        entity_description = SwitchEntityDescription(
            key="xbee_humidifier_valve_" + str(number + 1),
            name="Valve" if number != 3 else "Pressure Drop Valve",
            has_entity_name=True,
            icon="mdi:pipe-valve",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        switches.append(
            XBeeHumidifierSwitch(
                name="valve",
                number=number,
                coordinator=coordinator,
                entity_description=entity_description,
            )
        )

    entity_description = SwitchEntityDescription(
        key="xbee_humidifier_pump",
        name="Pump",
        has_entity_name=True,
        icon="mdi:water-pump",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.DIAGNOSTIC,
    )
    switches.append(
        XBeeHumidifierSwitch(
            name="pump",
            number=None,
            coordinator=coordinator,
            entity_description=entity_description,
        )
    )

    entity_description = SwitchEntityDescription(
        key="xbee_humidifier_pump_block",
        name="Pump Block",
        has_entity_name=True,
        icon="mdi:water-pump-off",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.CONFIG,
    )
    switches.append(
        XBeeHumidifierSwitch(
            name="pump_block",
            number=None,
            coordinator=coordinator,
            entity_description=entity_description,
        )
    )

    entity_description = SwitchEntityDescription(
        key="xbee_humidifier_fan",
        name="Fan",
        has_entity_name=True,
        icon="mdi:fan",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.DIAGNOSTIC,
    )
    switches.append(
        XBeeHumidifierSwitch(
            name="fan",
            number=None,
            coordinator=coordinator,
            entity_description=entity_description,
        )
    )

    entity_description = SwitchEntityDescription(
        key="xbee_humidifier_aux_led",
        name="AUX LED",
        has_entity_name=True,
        icon="mdi:led-off",
        device_class=SwitchDeviceClass.SWITCH,
        entity_category=EntityCategory.DIAGNOSTIC,
    )
    switches.append(
        XBeeHumidifierSwitch(
            name="aux_led",
            number=None,
            coordinator=coordinator,
            entity_description=entity_description,
        )
    )

    async_add_entities(switches)


class XBeeHumidifierSwitch(XBeeHumidifierEntity, SwitchEntity):
    """Representation of an XBee Humidifier control switches."""

    def __init__(
        self,
        name,
        number,
        coordinator: XBeeHumidifierDataUpdateCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""
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
            self._attr_is_on = value
            self.async_write_ha_state()

        subscriber_name = (
            self._name if self._number is None else self._name + "_" + str(self._number)
        )
        self.async_on_remove(
            self.coordinator.client.add_subscriber(subscriber_name, async_update_state)
        )
        if self._name == "pump_block":
            self.async_on_remove(
                self.coordinator.client.add_subscriber(
                    "device_reset", self._update_device
                )
            )

    async def _update_device(self):
        """Update device settings from HA on reset."""
        await self._turn(self._attr_is_on)

    async def _turn(self, is_on: bool) -> None:
        """Turn on or off the switch."""
        if self._number is None:
            resp = await self.coordinator.client.async_command(self._name, is_on)
        else:
            resp = await self.coordinator.client.async_command(
                self._name, self._number, is_on
            )

        if resp == "OK":
            self._attr_is_on = is_on
            self.async_write_ha_state()

    async def async_turn_on(self, **_: any) -> None:
        """Turn on the switch."""
        await self._turn(True)

    async def async_turn_off(self, **_: any) -> None:
        """Turn off the switch."""
        await self._turn(False)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data = self.coordinator.data.get(self._name)
        if data is not None and self._number is not None:
            data = data.get(self._number)
        self._attr_is_on = data

        self.schedule_update_ha_state()

    @property
    def available(self):
        """Return True if entity is available, always available for pump_block."""
        if self._name == "pump_block":
            return True
        return super().available
