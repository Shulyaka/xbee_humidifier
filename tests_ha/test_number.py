"""Test xbee_humidifier number."""

from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID

from .conftest import commands
from .const import IEEE

ENTITY = "number.xbee_humidifier_main_unit_pump_speed"


def test_test(hass):
    """Workaround for https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/discussions/160."""


async def test_number_remote_update(hass, data_from_device, test_config_entry):
    """Test remote update for number platform."""

    state = hass.states.get(ENTITY)
    assert state.state == "252"
    assert state.attributes.get("min") == 0
    assert state.attributes.get("max") == 1023
    assert state.attributes.get("step") == 1
    assert state.attributes.get("mode") == "slider"

    data_from_device(hass, IEEE, {"pump_speed": 126})
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY).state == "126"


async def test_number_local_update(hass, data_from_device, test_config_entry):
    """Test local update for number platform."""

    assert hass.states.get(ENTITY).state == "252"

    commands["pump_speed"].return_value = "OK"
    commands["pump_speed"].reset_mock()

    await hass.services.async_call(
        NUMBER,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: ENTITY, ATTR_VALUE: 327},
        blocking=True,
    )

    assert hass.states.get(ENTITY).state == "327"
    commands["pump_speed"].assert_called_once_with(327)
