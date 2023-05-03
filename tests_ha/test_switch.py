"""Test xbee_humidifier switches."""
from homeassistant.components.switch import (
    DOMAIN as SWITCH,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
import pytest

from .conftest import commands
from .const import IEEE

ENT_VALVE1 = "switch.xbee_humidifier_1_valve"
ENT_VALVE2 = "switch.xbee_humidifier_2_valve"
ENT_VALVE3 = "switch.xbee_humidifier_3_valve"
ENT_VALVE4 = "switch.xbee_humidifier_main_unit_pressure_drop_valve"
ENT_PUMP = "switch.xbee_humidifier_main_unit_pump"
ENT_PUMP_BLOCK = "switch.xbee_humidifier_main_unit_pump_block"
ENT_FAN = "switch.xbee_humidifier_main_unit_fan"
ENT_AUX_LED = "switch.xbee_humidifier_main_unit_aux_led"


def test_switch_init(hass, data_from_device, test_config_entry):
    """Test that all switch entities are created."""

    assert hass.states.get(ENT_VALVE1).state == STATE_OFF
    assert hass.states.get(ENT_VALVE2).state == STATE_OFF
    assert hass.states.get(ENT_VALVE3).state == STATE_OFF
    assert hass.states.get(ENT_VALVE4).state == STATE_OFF
    assert hass.states.get(ENT_PUMP).state == STATE_OFF
    assert hass.states.get(ENT_PUMP_BLOCK).state == STATE_OFF
    assert hass.states.get(ENT_FAN).state == STATE_OFF
    assert hass.states.get(ENT_AUX_LED).state == STATE_OFF


@pytest.mark.parametrize(
    "entity, command, number",
    (
        (ENT_VALVE1, "valve", 0),
        (ENT_VALVE2, "valve", 1),
        (ENT_VALVE3, "valve", 2),
        (ENT_VALVE4, "valve", 3),
        (ENT_PUMP, "pump", None),
        (ENT_PUMP_BLOCK, "pump_block", None),
        (ENT_FAN, "fan", None),
        (ENT_AUX_LED, "aux_led", None),
    ),
)
async def test_switch_services(
    hass, data_from_device, test_config_entry, entity, command, number
):
    """Test switch turn on/off."""

    assert hass.states.get(entity).state == STATE_OFF

    commands[command].return_value = "OK"
    commands[command].reset_mock()

    await hass.services.async_call(
        SWITCH,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )

    assert hass.states.get(entity).state == STATE_ON
    commands[command].assert_called_once_with(
        True if number is None else [number, True]
    )
    commands[command].reset_mock()

    await hass.services.async_call(
        SWITCH,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity},
        blocking=True,
    )

    assert hass.states.get(entity).state == STATE_OFF
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
        (ENT_PUMP, "pump"),
        (ENT_PUMP_BLOCK, "pump_block"),
        (ENT_FAN, "fan"),
        (ENT_AUX_LED, "aux_led"),
    ),
)
async def test_switch_remote_update(
    hass, data_from_device, test_config_entry, entity, data
):
    """Test switch remote on/off."""

    assert hass.states.get(entity).state == STATE_OFF

    data_from_device(hass, IEEE, {data: True})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_ON

    data_from_device(hass, IEEE, {data: False})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_OFF
