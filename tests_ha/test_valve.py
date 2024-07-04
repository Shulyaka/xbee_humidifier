"""Test xbee_humidifier valves."""

import pytest
from homeassistant.components.valve import (
    DOMAIN as VALVE,
    SERVICE_CLOSE_VALVE,
    SERVICE_OPEN_VALVE,
    STATE_CLOSED,
    STATE_OPEN,
)
from homeassistant.const import ATTR_ENTITY_ID

from .conftest import commands
from .const import IEEE

ENT_VALVE1 = "valve.xbee_humidifier_1_valve"
ENT_VALVE2 = "valve.xbee_humidifier_2_valve"
ENT_VALVE3 = "valve.xbee_humidifier_3_valve"
ENT_VALVE4 = "valve.xbee_humidifier_main_unit_pressure_drop_valve"


def test_switch_init(hass, data_from_device, test_config_entry):
    """Test that all valve entities are created."""

    assert hass.states.get(ENT_VALVE1).state == STATE_CLOSED
    assert hass.states.get(ENT_VALVE2).state == STATE_CLOSED
    assert hass.states.get(ENT_VALVE3).state == STATE_CLOSED
    assert hass.states.get(ENT_VALVE4).state == STATE_CLOSED


@pytest.mark.parametrize(
    "entity, command, number",
    (
        (ENT_VALVE1, "valve", 0),
        (ENT_VALVE2, "valve", 1),
        (ENT_VALVE3, "valve", 2),
        (ENT_VALVE4, "valve", 3),
    ),
)
async def test_switch_services(
    hass, data_from_device, test_config_entry, entity, command, number
):
    """Test valve open/close."""

    assert hass.states.get(entity).state == STATE_CLOSED

    commands[command].return_value = "OK"
    commands[command].reset_mock()

    await hass.services.async_call(
        VALVE,
        SERVICE_OPEN_VALVE,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )

    assert hass.states.get(entity).state == STATE_OPEN
    commands[command].assert_called_once_with(
        True if number is None else [number, True]
    )
    commands[command].reset_mock()

    await hass.services.async_call(
        VALVE,
        SERVICE_CLOSE_VALVE,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )

    assert hass.states.get(entity).state == STATE_CLOSED
    commands[command].assert_called_once_with(
        False if number is None else [number, False]
    )


@pytest.mark.parametrize(
    "entity, data",
    (
        (ENT_VALVE1, "valve_0"),
        (ENT_VALVE2, "valve_1"),
        (ENT_VALVE3, "valve_2"),
        (ENT_VALVE4, "valve_3"),
    ),
)
async def test_switch_remote_update(
    hass, data_from_device, test_config_entry, entity, data
):
    """Test valve remote open/close."""

    assert hass.states.get(entity).state == STATE_CLOSED

    data_from_device(hass, IEEE, {data: True})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_OPEN

    data_from_device(hass, IEEE, {data: False})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_CLOSED
