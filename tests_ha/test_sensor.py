"""Test xbee_humidifier sensors."""
import pytest

from .const import IEEE

ENTITY1 = "sensor.xbee_humidifier_main_unit_pump_temperature"
ENTITY2 = "sensor.xbee_humidifier_main_unit_pressure_in"


@pytest.mark.parametrize(
    "entity, data, value",
    (
        (ENTITY1, "pump_temp", 31),
        (ENTITY2, "pressure_in", 7),
    ),
)
async def test_sensor(hass, data_from_device, test_config_entry, entity, data, value):
    """Test sensor platform."""

    assert hass.states.get(entity).state == str(value)

    data_from_device(hass, IEEE, {data: value + 1})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state == str(value + 1)
