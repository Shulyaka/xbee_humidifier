"""Test xbee_humidifier sensors."""
import datetime as dt

import pytest

from .conftest import commands
from .const import IEEE

ENTITY1 = "sensor.xbee_humidifier_main_unit_pump_temperature"
ENTITY2 = "sensor.xbee_humidifier_main_unit_pressure_in"
ENTITY3 = "sensor.xbee_humidifier_main_unit_uptime"


@pytest.mark.parametrize(
    "entity, data, value, newdata, newvalue",
    (
        (ENTITY1, "pump_temp", "31", 32, "32"),
        (ENTITY2, "pressure_in", "7.00", 4158, "7.59"),
        (ENTITY3, "uptime", "2023", 1800000000, "2027"),
    ),
)
async def test_sensor(
    hass, data_from_device, test_config_entry, entity, data, value, newdata, newvalue
):
    """Test sensor platform."""

    assert hass.states.get(entity).state[:4] == value

    data_from_device(hass, IEEE, {data: newdata})
    await hass.async_block_till_done()

    assert hass.states.get(entity).state[:4] == newvalue


async def test_uptime_set(hass, data_from_device, test_config_entry):
    """Test absolute uptime set if relative uptime is returned from the device."""

    commands["uptime"].reset_mock()

    data_from_device(hass, IEEE, {"uptime": -30})
    await hass.async_block_till_done()

    assert commands["uptime"].call_count == 1
    assert (
        abs(
            commands["uptime"].call_args[0][0][0]
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 1
    )
    assert commands["uptime"].call_args[0][0][1] == -30

    assert (
        hass.states.get(ENTITY3).state
        == (dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(seconds=-30))
        .replace(microsecond=0)
        .isoformat()
    )
