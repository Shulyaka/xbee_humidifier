"""Test xbee_humidifier binary sensors."""
from homeassistant.const import STATE_OFF, STATE_ON
import pytest

from .const import IEEE

ENTITY1 = "binary_sensor.xbee_humidifier_1_working"
ENTITY2 = "binary_sensor.xbee_humidifier_2_working"
ENTITY3 = "binary_sensor.xbee_humidifier_3_working"


@pytest.mark.parametrize(
    "entity, data",
    (
        (ENTITY1, "working_0"),
        (ENTITY2, "working_1"),
        (ENTITY3, "working_2"),
    ),
)
async def test_binary_sensor(hass, data_from_device, test_config_entry, entity, data):
    """Test binary_sensor platform."""

    assert hass.states.get(entity).state == STATE_OFF

    data_from_device(hass, IEEE, {data: True})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_ON

    data_from_device(hass, IEEE, {data: False})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == STATE_OFF
