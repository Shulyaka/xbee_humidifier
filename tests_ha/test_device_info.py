"""Test device registry links and entity behavior after registration."""

import asyncio
import logging
from collections.abc import Callable, Iterator
from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
    label_registry as lr,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbee_humidifier import CONF_SENSOR
from custom_components.xbee_humidifier.const import DOMAIN
from custom_components.xbee_humidifier.coordinator import (
    XBeeHumidifierDataUpdateCoordinator,
)

from .const import IEEE, MOCK_CONFIG, MOCK_OPTIONS

pytestmark = pytest.mark.usefixtures("data_from_device")


@pytest.fixture
def device_registrations(
    device_registry: dr.DeviceRegistry,
) -> Iterator[MagicMock]:
    """Capture metadata passed to the real device registry."""
    with patch.object(
        device_registry,
        "async_get_or_create",
        wraps=device_registry.async_get_or_create,
    ) as registrations:
        yield registrations


async def test_device_topology(
    device_registrations: MagicMock,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    zha_device: dr.DeviceEntry,
    test_config_entry: MockConfigEntry,
) -> None:
    """The main unit links to ZHA and contains all three zone child devices."""
    assert device_registrations.called
    assert all(
        "via_device" not in call.kwargs for call in device_registrations.call_args_list
    )
    main_device = device_registry.async_get_device_by_identifier(
        (DOMAIN, IEEE), test_config_entry.entry_id
    )
    assert main_device is not None
    assert main_device.via_device_id == zha_device.id

    device_ids = {main_device.id}
    for number in range(3):
        device = device_registry.async_get_child_device_by_identifier(
            (DOMAIN, f"{IEEE}-{number}"), test_config_entry.entry_id
        )
        assert device is not None
        assert device.parent_device_id == main_device.id
        device_ids.add(device.id)

    entities = er.async_entries_for_config_entry(
        entity_registry, test_config_entry.entry_id
    )
    assert {entity.device_id for entity in entities} == device_ids
    assert (
        len(
            dr.async_entries_for_config_entry(
                device_registry, test_config_entry.entry_id
            )
        )
        == 1
    )
    assert (
        len(
            dr.async_child_entries_for_config_entry(
                device_registry, test_config_entry.entry_id
            )
        )
        == 3
    )
    pressure_valve = entity_registry.async_get(
        "valve.xbee_humidifier_main_unit_pressure_drop_valve"
    )
    assert pressure_valve is not None
    assert pressure_valve.device_id == main_device.id


async def test_device_and_entity_ids_survive_reload(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    test_config_entry: MockConfigEntry,
) -> None:
    """Registration on reload preserves registry identities and user names."""
    humidifier = entity_registry.async_get("humidifier.xbee_humidifier_1_humidifier")
    assert humidifier is not None
    entity_registry.async_update_entity(
        humidifier.entity_id, new_entity_id="humidifier.living_room"
    )
    device_registry.async_update_child_device(
        humidifier.device_id, name_by_user="Living room"
    )

    main_device = device_registry.async_get_device_by_identifier(
        (DOMAIN, IEEE), test_config_entry.entry_id
    )
    assert main_device is not None
    device_registry.async_update_device(main_device.id, name_by_user="Humidifier plant")
    await hass.async_block_till_done()

    entities_before = {
        entity.entity_id: (entity.id, entity.unique_id, entity.device_id)
        for entity in er.async_entries_for_config_entry(
            entity_registry, test_config_entry.entry_id
        )
    }
    devices_before = {
        device.id: (
            device.identifiers,
            device.via_device_id,
            device.name_by_user,
            device.name,
            device.model,
            device.manufacturer,
            device.hw_version,
            device.sw_version,
        )
        for device in dr.async_entries_for_config_entry(
            device_registry, test_config_entry.entry_id
        )
    }

    children_before = {
        device.id: (
            device.identifiers,
            device.parent_device_id,
            device.name_by_user,
            device.name,
            device.area_id,
            device.labels,
        )
        for device in dr.async_child_entries_for_config_entry(
            device_registry, test_config_entry.entry_id
        )
    }

    assert await hass.config_entries.async_reload(test_config_entry.entry_id)
    await hass.async_block_till_done()

    assert {
        entity.entity_id: (entity.id, entity.unique_id, entity.device_id)
        for entity in er.async_entries_for_config_entry(
            entity_registry, test_config_entry.entry_id
        )
    } == entities_before
    assert {
        device.id: (
            device.identifiers,
            device.via_device_id,
            device.name_by_user,
            device.name,
            device.model,
            device.manufacturer,
            device.hw_version,
            device.sw_version,
        )
        for device in dr.async_entries_for_config_entry(
            device_registry, test_config_entry.entry_id
        )
    } == devices_before
    assert {
        device.id: (
            device.identifiers,
            device.parent_device_id,
            device.name_by_user,
            device.name,
            device.area_id,
            device.labels,
        )
        for device in dr.async_child_entries_for_config_entry(
            device_registry, test_config_entry.entry_id
        )
    } == children_before
    assert hass.states.get("humidifier.living_room") is not None
    assert hass.states.get("humidifier.xbee_humidifier_1_humidifier") is None


async def test_existing_zones_become_child_devices(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    label_registry: lr.LabelRegistry,
    zha_device: dr.DeviceEntry,
) -> None:
    """Adopt existing zones without changing registry identities or user settings."""

    def legacy_zone_info(
        *, identifiers: set[tuple[str, str]], name: str, parent_device_id: str
    ) -> dr.DeviceInfo:
        return dr.DeviceInfo(
            identifiers=identifiers,
            name=name,
            via_device_id=parent_device_id,
            model="XBee3",
            manufacturer="Digi",
            hw_version="4247",
            sw_version="1014",
        )

    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, options=MOCK_OPTIONS)
    entry.add_to_hass(hass)
    try:
        with patch(
            "custom_components.xbee_humidifier.entity.ChildDeviceInfo",
            side_effect=legacy_zone_info,
        ):
            assert await hass.config_entries.async_setup(entry.entry_id)
            await hass.async_block_till_done()

        main_device = device_registry.async_get_device_by_identifier(
            (DOMAIN, IEEE), entry.entry_id
        )
        assert main_device is not None
        assert main_device.via_device_id == zha_device.id
        assert not dr.async_child_entries_for_config_entry(
            device_registry, entry.entry_id
        )
        label = label_registry.async_create("Humidification")
        old_zones = {}
        for number in range(3):
            device = device_registry.async_get_device_by_identifier(
                (DOMAIN, f"{IEEE}-{number}"), entry.entry_id
            )
            assert device is not None
            area = area_registry.async_create(f"Zone {number + 1}")
            old_zones[number] = device_registry.async_update_device(
                device.id,
                name_by_user=f"Room humidifier {number + 1}",
                area_id=area.id,
                labels={label.label_id},
            )
            entity_registry.async_update_entity(
                f"humidifier.xbee_humidifier_{number + 1}_humidifier",
                new_entity_id=f"humidifier.room_{number + 1}",
            )
        await hass.async_block_till_done()
        entities_before = {
            entity.entity_id: (entity.id, entity.unique_id, entity.device_id)
            for entity in er.async_entries_for_config_entry(
                entity_registry, entry.entry_id
            )
        }

        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        main_after = device_registry.async_get_device_by_identifier(
            (DOMAIN, IEEE), entry.entry_id
        )
        assert main_after is not None
        assert main_after.id == main_device.id
        assert main_after.via_device_id == zha_device.id
        assert (
            len(dr.async_entries_for_config_entry(device_registry, entry.entry_id)) == 1
        )
        assert (
            len(
                dr.async_child_entries_for_config_entry(device_registry, entry.entry_id)
            )
            == 3
        )
        for number, previous_device in old_zones.items():
            child = device_registry.async_get_child_device_by_identifier(
                (DOMAIN, f"{IEEE}-{number}"), entry.entry_id
            )
            assert child is not None
            assert child.id == previous_device.id
            assert child.parent_device_id == main_device.id
            assert child.identifiers == previous_device.identifiers
            assert child.name == previous_device.name
            assert child.name_by_user == previous_device.name_by_user
            assert child.area_id == previous_device.area_id
            assert child.labels == previous_device.labels
            assert hass.states.get(f"humidifier.room_{number + 1}") is not None
        assert {
            entity.entity_id: (entity.id, entity.unique_id, entity.device_id)
            for entity in er.async_entries_for_config_entry(
                entity_registry, entry.entry_id
            )
        } == entities_before
    finally:
        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()


async def test_missing_zha_device_retries(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    zha_device: dr.DeviceEntry,
) -> None:
    """Missing ZHA ownership delays setup until the physical device is registered."""
    device_registry.async_remove_device(zha_device.id)
    unrelated_entry = MockConfigEntry(domain="other", entry_id="other")
    unrelated_entry.add_to_hass(hass)
    unrelated_device = device_registry.async_get_or_create(
        config_entry_id=unrelated_entry.entry_id, identifiers={("zha", IEEE)}
    )
    entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, options=MOCK_OPTIONS)
    entry.add_to_hass(hass)
    try:
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.SETUP_RETRY
        assert "XBee device is not registered with ZHA" in entry.reason
        assert (
            device_registry.async_get_device_by_identifier(
                (DOMAIN, IEEE), entry.entry_id
            )
            is None
        )

        physical_device = device_registry.async_get_or_create(
            config_entry_id="test_zha", identifiers={("zha", IEEE)}, name="XBee"
        )
        assert physical_device.id != unrelated_device.id
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.state is ConfigEntryState.LOADED
        main_device = device_registry.async_get_device_by_identifier(
            (DOMAIN, IEEE), entry.entry_id
        )
        assert main_device is not None
        assert main_device.via_device_id == physical_device.id
    finally:
        await hass.config_entries.async_remove(entry.entry_id)
        await hass.async_block_till_done()


async def test_each_humidifier_tracks_its_sensor(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    data_from_device: Callable[[HomeAssistant, str, dict[str, object]], None],
    test_config_entry: MockConfigEntry,
) -> None:
    """All three sensor callbacks keep their device after an awaited command."""
    options = deepcopy(MOCK_OPTIONS)
    for number in range(3):
        options[f"humidifier_{number}"][CONF_SENSOR] = f"sensor.humidity_{number}"
    hass.config_entries.async_update_entry(test_config_entry, options=options)
    await hass.async_block_till_done()
    coordinator: XBeeHumidifierDataUpdateCoordinator = hass.data[DOMAIN][
        test_config_entry.entry_id
    ]
    original_command = coordinator.client.async_command
    pending_commands: asyncio.Queue[tuple[object, ...]] = asyncio.Queue()
    resume = asyncio.Event()

    async def send_command(command: str, *args: object, **kwargs: object) -> object:
        assert command == "cur_hum"
        pending_commands.put_nowait(args)
        await resume.wait()
        return await original_command(command, *args, **kwargs)

    data_from_device(
        hass, IEEE, {"available_0": True, "available_1": True, "available_2": True}
    )
    await hass.async_block_till_done()

    with patch.object(coordinator.client, "async_command", side_effect=send_command):
        for number, humidity in enumerate((31, 42, 53)):
            hass.states.async_set(f"sensor.humidity_{number}", str(humidity))
        try:
            async with asyncio.timeout(5):
                sent_commands = [await pending_commands.get() for _ in range(3)]
            assert sorted(sent_commands) == [(0, 31.0), (1, 42.0), (2, 53.0)]
            data_from_device(hass, IEEE, {"available_0": False})
        finally:
            resume.set()
        await hass.async_block_till_done()

    assert (
        hass.states.get("humidifier.xbee_humidifier_1_humidifier").state
        == "unavailable"
    )
    assert hass.states.get("humidifier.xbee_humidifier_2_humidifier").state == "off"
    assert hass.states.get("humidifier.xbee_humidifier_3_humidifier").state == "off"

    data_from_device(hass, IEEE, {"available_0": True})
    await hass.async_block_till_done()
    for number, humidity in enumerate((31, 42, 53), start=1):
        state = hass.states.get(f"humidifier.xbee_humidifier_{number}_humidifier")
        assert state is not None
        assert state.attributes["current_humidity"] == humidity

    assert not any(record.levelno >= logging.ERROR for record in caplog.records)
