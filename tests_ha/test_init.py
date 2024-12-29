"""Test xbee_humidifier."""

import datetime as dt
from unittest.mock import patch

import pytest
from homeassistant.components.humidifier import DOMAIN as HUMIDIFIER, SERVICE_SET_MODE
from homeassistant.const import ATTR_ENTITY_ID, ATTR_MODE
from homeassistant.core import State
from pytest_homeassistant_custom_component.common import mock_restore_cache

from .conftest import commands
from .const import IEEE

ENTITY1 = "humidifier.xbee_humidifier_1_humidifier"
ENTITY2 = "humidifier.xbee_humidifier_2_humidifier"
ENTITY3 = "humidifier.xbee_humidifier_3_humidifier"


def test_test(hass):
    """Workaround for https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/discussions/160."""


async def test_init_default(hass, caplog, data_from_device, test_config_entry):
    """Test component initialization with no device or history data."""

    assert len(commands) == 20
    commands["bind"].assert_called_once_with()
    commands["unique_id"].assert_called_once_with()
    commands["atcmd"].assert_called_once_with("VL")
    commands["pump"].assert_called_once_with()
    commands["pump_temp"].assert_called_once_with()
    assert commands["pump_block"].call_count == 0
    commands["pressure_in"].assert_called_once_with()
    commands["fan"].assert_called_once_with()
    commands["aux_led"].assert_called_once_with()
    commands["pump_speed"].assert_called_once_with()
    commands["reset_cause"].assert_called_once_with()
    assert commands["uptime"].call_count == 2
    assert commands["uptime"].call_args_list[0][0] == ()
    assert (
        abs(
            commands["uptime"].call_args_list[1][0][0]
            + 10
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 2
    )
    assert commands["valve"].call_count == 4
    assert commands["valve"].call_args_list[0][0][0] == 0
    assert commands["valve"].call_args_list[1][0][0] == 1
    assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["valve"].call_args_list[3][0][0] == 3
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == [0, None]
    assert commands["cur_hum"].call_args_list[1][0][0] == [1, None]
    assert commands["cur_hum"].call_args_list[2][0][0] == [2, None]
    assert commands["target_hum"].call_count == 5
    assert commands["target_hum"].call_args_list[0][0][0] == [0, 32]
    assert commands["target_hum"].call_args_list[1][0][0] == [0, 42]
    assert commands["target_hum"].call_args_list[2][0][0] == [1, 32]
    assert commands["target_hum"].call_args_list[3][0][0] == [1, 42]
    assert commands["target_hum"].call_args_list[4][0][0] == [2, 42]
    assert commands["mode"].call_count == 5
    assert commands["mode"].call_args_list[0][0][0] == [0, "away"]
    assert commands["mode"].call_args_list[1][0][0] == [0, "normal"]
    assert commands["mode"].call_args_list[2][0][0] == [1, "away"]
    assert commands["mode"].call_args_list[3][0][0] == [1, "normal"]
    assert commands["mode"].call_args_list[4][0][0] == [2, "normal"]
    assert commands["sav_hum"].call_count == 0
    assert commands["available"].call_count == 0
    assert commands["zone"].call_count == 0
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == [0, False]
    assert commands["hum"].call_args_list[1][0][0] == [1, False]
    assert commands["hum"].call_args_list[2][0][0] == [2, False]

    data_from_device(hass, IEEE, {"log": {"msg": "Test log", "sev": 20}})
    await hass.async_block_till_done()
    assert "Test log" in caplog.text

    data_from_device(hass, IEEE, {"available_0": True})
    data_from_device(hass, IEEE, {"available_1": True})
    data_from_device(hass, IEEE, {"available_2": True})
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY1).state == "off"
    assert hass.states.get(ENTITY1).attributes["humidity"] == 42
    assert hass.states.get(ENTITY1).attributes["saved_humidity"] == 32
    assert hass.states.get(ENTITY2).state == "off"
    assert hass.states.get(ENTITY2).attributes["humidity"] == 42
    assert hass.states.get(ENTITY2).attributes["saved_humidity"] == 32
    assert hass.states.get(ENTITY3).state == "off"
    assert hass.states.get(ENTITY3).attributes["humidity"] == 42
    assert "saved_humidity" not in hass.states.get(ENTITY3).attributes


@pytest.fixture
def test_1():
    """Configure the data from the initialized device."""
    commands["uptime"].return_value = 1700000000
    commands["available"].return_value = True
    commands["hum"]([0, True])
    commands["hum"]([1, False])
    commands["hum"]([2, True])
    commands["target_hum"]([0, 40])
    commands["target_hum"]([1, 41])
    commands["target_hum"]([2, 42])
    commands["hum"].reset_mock()
    commands["target_hum"].reset_mock()


async def test_init_from_device(hass, data_from_device, test_1, test_config_entry):
    """Test component initialization from device data."""

    assert len(commands) == 20
    commands["bind"].assert_called_once_with()
    commands["uptime"].assert_called_once_with()
    assert commands["sav_hum"].call_count == 3
    assert commands["sav_hum"].call_args_list[0][0][0] == 0
    assert commands["sav_hum"].call_args_list[1][0][0] == 1
    assert commands["sav_hum"].call_args_list[2][0][0] == 2
    assert commands["available"].call_count == 3
    assert commands["available"].call_args_list[0][0][0] == 0
    assert commands["available"].call_args_list[1][0][0] == 1
    assert commands["available"].call_args_list[2][0][0] == 2
    assert commands["zone"].call_count == 3
    assert commands["zone"].call_args_list[0][0][0] == 0
    assert commands["zone"].call_args_list[1][0][0] == 1
    assert commands["zone"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == 0
    assert commands["hum"].call_args_list[1][0][0] == 1
    assert commands["hum"].call_args_list[2][0][0] == 2
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == 0
    assert commands["cur_hum"].call_args_list[1][0][0] == 1
    assert commands["cur_hum"].call_args_list[2][0][0] == 2
    assert commands["target_hum"].call_count == 3
    assert commands["target_hum"].call_args_list[0][0][0] == 0
    assert commands["target_hum"].call_args_list[1][0][0] == 1
    assert commands["target_hum"].call_args_list[2][0][0] == 2
    assert commands["mode"].call_count == 3
    assert commands["mode"].call_args_list[0][0][0] == 0
    assert commands["mode"].call_args_list[1][0][0] == 1
    assert commands["mode"].call_args_list[2][0][0] == 2

    assert hass.states.get(ENTITY1).state == "on"
    assert hass.states.get(ENTITY1).attributes["humidity"] == 40
    assert hass.states.get(ENTITY2).state == "off"
    assert hass.states.get(ENTITY2).attributes["humidity"] == 41
    assert hass.states.get(ENTITY3).state == "on"
    assert hass.states.get(ENTITY3).attributes["humidity"] == 42


@pytest.fixture
def restore_state_1(hass):
    """Prepare restore state."""
    states = []

    restored_attributes1 = {
        "min_humidity": 15,
        "max_humidity": 100,
        "available_modes": ["normal", "away"],
        "action": "idle",
        "current_humidity": 48,
        "humidity": 45,
        "mode": "normal",
        "saved_humidity": 40,
        "attribution": "Denis Shulyaka",
        "device_class": "humidifier",
        "icon": "mdi:air-humidifier",
        "supported_features": 1,
    }

    restored_attributes2 = restored_attributes1.copy()
    restored_attributes2["humidity"] = 46
    restored_attributes2["mode"] = "away"

    restored_attributes3 = restored_attributes1.copy()
    restored_attributes3["humidity"] = 47

    fake_state = State(
        ENTITY1,
        "on",
        restored_attributes1,
    )
    states.append(fake_state)

    fake_state = State(
        ENTITY2,
        "off",
        restored_attributes2,
    )
    states.append(fake_state)

    fake_state = State(
        ENTITY3,
        "on",
        restored_attributes3,
    )
    states.append(fake_state)

    mock_restore_cache(hass, states)


async def test_init_from_last_state(
    hass, data_from_device, restore_state_1, test_config_entry
):
    """Test component initialization from RestoreEntity last state."""

    assert len(commands) == 20
    commands["bind"].assert_called_once_with()
    commands["unique_id"].assert_called_once_with()
    commands["atcmd"].assert_called_once_with("VL")
    commands["pump"].assert_called_once_with()
    commands["pump_temp"].assert_called_once_with()
    assert commands["pump_block"].call_count == 0
    commands["pressure_in"].assert_called_once_with()
    commands["fan"].assert_called_once_with()
    commands["aux_led"].assert_called_once_with()
    commands["pump_speed"].assert_called_once_with()
    commands["reset_cause"].assert_called_once_with()
    assert commands["uptime"].call_count == 2
    assert commands["uptime"].call_args_list[0][0] == ()
    assert (
        abs(
            commands["uptime"].call_args_list[1][0][0]
            + 10
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 2
    )
    assert commands["valve"].call_count == 4
    assert commands["valve"].call_args_list[0][0][0] == 0
    assert commands["valve"].call_args_list[1][0][0] == 1
    assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["valve"].call_args_list[3][0][0] == 3
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == [0, None]
    assert commands["cur_hum"].call_args_list[1][0][0] == [1, None]
    assert commands["cur_hum"].call_args_list[2][0][0] == [2, None]
    assert commands["target_hum"].call_count == 5
    assert commands["target_hum"].call_args_list[0][0][0] == [0, 40]
    assert commands["target_hum"].call_args_list[1][0][0] == [0, 45]
    assert commands["target_hum"].call_args_list[2][0][0] == [1, 40]
    assert commands["target_hum"].call_args_list[3][0][0] == [1, 46]
    assert commands["target_hum"].call_args_list[4][0][0] == [2, 47]
    assert commands["mode"].call_count == 5
    assert commands["mode"].call_args_list[0][0][0] == [0, "away"]
    assert commands["mode"].call_args_list[1][0][0] == [0, "normal"]
    assert commands["mode"].call_args_list[2][0][0] == [1, "normal"]
    assert commands["mode"].call_args_list[3][0][0] == [1, "away"]
    assert commands["mode"].call_args_list[4][0][0] == [2, "normal"]
    assert commands["sav_hum"].call_count == 0
    assert commands["available"].call_count == 0
    assert commands["zone"].call_count == 0
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == [0, True]
    assert commands["hum"].call_args_list[1][0][0] == [1, False]
    assert commands["hum"].call_args_list[2][0][0] == [2, True]

    data_from_device(hass, IEEE, {"available_0": True})
    data_from_device(hass, IEEE, {"available_1": True})
    data_from_device(hass, IEEE, {"available_2": True})
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY1).state == "on"
    assert hass.states.get(ENTITY1).attributes["humidity"] == 45
    assert hass.states.get(ENTITY1).attributes["saved_humidity"] == 40
    assert hass.states.get(ENTITY1).attributes["mode"] == "normal"
    assert hass.states.get(ENTITY2).state == "off"
    assert hass.states.get(ENTITY2).attributes["humidity"] == 46
    assert hass.states.get(ENTITY2).attributes["saved_humidity"] == 40
    assert hass.states.get(ENTITY2).attributes["mode"] == "away"
    assert hass.states.get(ENTITY3).state == "on"
    assert hass.states.get(ENTITY3).attributes["humidity"] == 47


async def test_init_from_history(hass, data_from_device, test_config_entry):
    """Test component initialization from recorder history."""
    for cmd in [
        "uptime",
        "bind",
        "reset_cause",
        "unique_id",
        "atcmd",
        "pump",
        "pump_temp",
        "pressure_in",
        "fan",
        "aux_led",
        "pump_speed",
        "valve",
        "cur_hum",
        "target_hum",
        "mode",
        "hum",
    ]:
        commands[cmd].reset_mock()
    commands["uptime"].return_value = -17

    states = {}

    restored_attributes1 = {
        "min_humidity": 15,
        "max_humidity": 100,
        "available_modes": ["normal", "away"],
        "action": "idle",
        "current_humidity": 48,
        "humidity": 45,
        "mode": "normal",
        "saved_humidity": 40,
        "attribution": "Denis Shulyaka",
        "device_class": "humidifier",
        "icon": "mdi:air-humidifier",
        "supported_features": 1,
    }

    restored_attributes2 = restored_attributes1.copy()
    restored_attributes2["humidity"] = 46
    restored_attributes2["mode"] = "away"

    restored_attributes3 = restored_attributes1.copy()
    restored_attributes3["humidity"] = 47

    fake_state = State(
        ENTITY1,
        "on",
        restored_attributes1,
    )
    states[ENTITY1] = [fake_state]

    fake_state = State(
        ENTITY2,
        "off",
        restored_attributes2,
    )
    states[ENTITY2] = [fake_state]

    fake_state = State(
        ENTITY3,
        "on",
        restored_attributes3,
    )
    states[ENTITY3] = [fake_state]

    with patch(
        "homeassistant.components.recorder.history.get_last_state_changes",
        return_value=states,
    ) as mock_history:
        assert await hass.config_entries.async_reload(test_config_entry.entry_id)
        await hass.async_block_till_done()
        assert mock_history.call_count == 3

    assert len(commands) == 20
    commands["bind"].assert_called_once_with()
    commands["unique_id"].assert_called_once_with()
    commands["atcmd"].assert_called_once_with("VL")
    commands["pump"].assert_called_once_with()
    commands["pump_temp"].assert_called_once_with()
    assert commands["pump_block"].call_count == 0
    commands["pressure_in"].assert_called_once_with()
    commands["fan"].assert_called_once_with()
    commands["aux_led"].assert_called_once_with()
    commands["pump_speed"].assert_called_once_with()
    commands["reset_cause"].assert_called_once_with()
    assert commands["uptime"].call_count == 2
    assert commands["uptime"].call_args_list[0][0] == ()
    assert (
        abs(
            commands["uptime"].call_args_list[1][0][0]
            + 17
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 2
    )
    assert commands["valve"].call_count == 4
    assert commands["valve"].call_args_list[0][0][0] == 0
    assert commands["valve"].call_args_list[1][0][0] == 1
    assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["valve"].call_args_list[3][0][0] == 3
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == [0, None]
    assert commands["cur_hum"].call_args_list[1][0][0] == [1, None]
    assert commands["cur_hum"].call_args_list[2][0][0] == [2, None]
    assert commands["target_hum"].call_count == 5
    assert commands["target_hum"].call_args_list[0][0][0] == [0, 40]
    assert commands["target_hum"].call_args_list[1][0][0] == [0, 45]
    assert commands["target_hum"].call_args_list[2][0][0] == [1, 40]
    assert commands["target_hum"].call_args_list[3][0][0] == [1, 46]
    assert commands["target_hum"].call_args_list[4][0][0] == [2, 47]
    assert commands["mode"].call_count == 5
    assert commands["mode"].call_args_list[0][0][0] == [0, "away"]
    assert commands["mode"].call_args_list[1][0][0] == [0, "normal"]
    assert commands["mode"].call_args_list[2][0][0] == [1, "normal"]
    assert commands["mode"].call_args_list[3][0][0] == [1, "away"]
    assert commands["mode"].call_args_list[4][0][0] == [2, "normal"]
    assert commands["sav_hum"].call_count == 0
    assert commands["available"].call_count == 0
    assert commands["zone"].call_count == 0
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == [0, True]
    assert commands["hum"].call_args_list[1][0][0] == [1, False]
    assert commands["hum"].call_args_list[2][0][0] == [2, True]

    data_from_device(hass, IEEE, {"available_0": True})
    data_from_device(hass, IEEE, {"available_1": True})
    data_from_device(hass, IEEE, {"available_2": True})
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY1).state == "on"
    assert hass.states.get(ENTITY1).attributes["humidity"] == 45
    assert hass.states.get(ENTITY1).attributes["saved_humidity"] == 40
    assert hass.states.get(ENTITY1).attributes["mode"] == "normal"
    assert hass.states.get(ENTITY2).state == "off"
    assert hass.states.get(ENTITY2).attributes["humidity"] == 46
    assert hass.states.get(ENTITY2).attributes["saved_humidity"] == 40
    assert hass.states.get(ENTITY2).attributes["mode"] == "away"
    assert hass.states.get(ENTITY3).state == "on"
    assert hass.states.get(ENTITY3).attributes["humidity"] == 47


async def test_refresh(hass, data_from_device, test_config_entry):
    """Test reinitialize on device reset."""

    data_from_device(hass, IEEE, {"available_1": True})
    await hass.async_block_till_done()

    commands["mode"].return_value = "OK"
    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_SET_MODE,
        service_data={ATTR_ENTITY_ID: ENTITY2, ATTR_MODE: "away"},
        blocking=True,
    )

    hass.states.async_set("sensor.test2", "45.0")
    hass.states.async_set("sensor.test3", "46.3")
    await hass.async_block_till_done()

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["uptime"].return_value = 0
    commands["hum"].reset_mock()
    commands["sav_hum"].reset_mock()
    commands["available"].reset_mock()
    commands["zone"].reset_mock()
    commands["target_hum"].reset_mock()
    commands["cur_hum"].reset_mock()
    commands["pump_block"].reset_mock()
    commands["mode"].reset_mock()
    commands["mode"].return_value = "normal"
    data_from_device(hass, IEEE, {"uptime": 0})
    await hass.async_block_till_done()
    commands["bind"].assert_called_once_with()
    assert commands["mode"].call_count == 5
    assert commands["mode"].call_args_list[0][0][0] == [0, "away"]
    assert commands["mode"].call_args_list[1][0][0] == [0, "normal"]
    assert commands["mode"].call_args_list[2][0][0] == [1, "normal"]
    assert commands["mode"].call_args_list[3][0][0] == [1, "away"]
    assert commands["mode"].call_args_list[4][0][0] == [2, "normal"]
    assert commands["target_hum"].call_count == 5
    assert commands["target_hum"].call_args_list[0][0][0] == [0, 32]
    assert commands["target_hum"].call_args_list[1][0][0] == [0, 42]
    assert commands["target_hum"].call_args_list[2][0][0] == [1, 42]
    assert commands["target_hum"].call_args_list[3][0][0] == [1, 32]
    assert commands["target_hum"].call_args_list[4][0][0] == [2, 42]
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == [0, None]
    assert commands["cur_hum"].call_args_list[1][0][0] == [1, 45.0]
    assert commands["cur_hum"].call_args_list[2][0][0] == [2, 46.3]
    assert commands["sav_hum"].call_count == 0
    assert commands["available"].call_count == 0
    assert commands["zone"].call_count == 0
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == [0, False]
    assert commands["hum"].call_args_list[1][0][0] == [1, False]
    assert commands["hum"].call_args_list[2][0][0] == [2, False]
    commands["pump_block"].assert_called_once_with(False)
    assert commands["uptime"].call_count == 1
    assert (
        abs(
            commands["uptime"].call_args_list[0][0][0]
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 1.5
    )


async def test_reload(hass, data_from_device, test_config_entry):
    """Test config entry reload."""

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["hum"].reset_mock()
    commands["sav_hum"].reset_mock()
    commands["available"].reset_mock()
    commands["available"].return_value = True
    commands["zone"].reset_mock()
    commands["target_hum"].reset_mock()
    commands["mode"].reset_mock()
    commands["cur_hum"].reset_mock()
    commands["cur_hum"].return_value = 41.0

    new_options = test_config_entry.options.copy()
    new_options["humidifier_0"] = test_config_entry.options["humidifier_0"].copy()
    new_options["humidifier_0"]["target_sensor"] = "sensor.test4"

    assert test_config_entry.options != new_options
    assert hass.config_entries.async_update_entry(
        test_config_entry, options=new_options
    )
    await hass.async_block_till_done()

    commands["bind"].assert_called_once_with()
    commands["uptime"].assert_called_once_with()
    assert commands["sav_hum"].call_count == 3
    assert commands["sav_hum"].call_args_list[0][0][0] == 0
    assert commands["sav_hum"].call_args_list[1][0][0] == 1
    assert commands["sav_hum"].call_args_list[2][0][0] == 2
    assert commands["available"].call_count == 3
    assert commands["available"].call_args_list[0][0][0] == 0
    assert commands["available"].call_args_list[1][0][0] == 1
    assert commands["available"].call_args_list[2][0][0] == 2
    assert commands["zone"].call_count == 3
    assert commands["zone"].call_args_list[0][0][0] == 0
    assert commands["zone"].call_args_list[1][0][0] == 1
    assert commands["zone"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == 0
    assert commands["hum"].call_args_list[1][0][0] == 1
    assert commands["hum"].call_args_list[2][0][0] == 2
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == 0
    assert commands["cur_hum"].call_args_list[1][0][0] == 1
    assert commands["cur_hum"].call_args_list[2][0][0] == 2
    assert commands["target_hum"].call_count == 3
    assert commands["target_hum"].call_args_list[0][0][0] == 0
    assert commands["target_hum"].call_args_list[1][0][0] == 1
    assert commands["target_hum"].call_args_list[2][0][0] == 2
    assert commands["mode"].call_count == 3
    assert commands["mode"].call_args_list[0][0][0] == 0
    assert commands["mode"].call_args_list[1][0][0] == 1
    assert commands["mode"].call_args_list[2][0][0] == 2


async def test_coordinator_update(hass, data_from_device, test_config_entry):
    """Test coordinator data update."""

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["hum"].reset_mock()
    commands["sav_hum"].reset_mock()
    commands["available"].reset_mock()
    commands["zone"].reset_mock()
    commands["target_hum"].reset_mock()
    commands["mode"].reset_mock()
    commands["cur_hum"].reset_mock()

    coordinator = hass.data["xbee_humidifier"][test_config_entry.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    commands["bind"].assert_called_once_with()
    commands["uptime"].assert_called_once_with()
    assert commands["sav_hum"].call_count == 3
    assert commands["sav_hum"].call_args_list[0][0][0] == 0
    assert commands["sav_hum"].call_args_list[1][0][0] == 1
    assert commands["sav_hum"].call_args_list[2][0][0] == 2
    assert commands["available"].call_count == 3
    assert commands["available"].call_args_list[0][0][0] == 0
    assert commands["available"].call_args_list[1][0][0] == 1
    assert commands["available"].call_args_list[2][0][0] == 2
    assert commands["zone"].call_count == 3
    assert commands["zone"].call_args_list[0][0][0] == 0
    assert commands["zone"].call_args_list[1][0][0] == 1
    assert commands["zone"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == 0
    assert commands["hum"].call_args_list[1][0][0] == 1
    assert commands["hum"].call_args_list[2][0][0] == 2
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == 0
    assert commands["cur_hum"].call_args_list[1][0][0] == 1
    assert commands["cur_hum"].call_args_list[2][0][0] == 2
    assert commands["target_hum"].call_count == 3
    assert commands["target_hum"].call_args_list[0][0][0] == 0
    assert commands["target_hum"].call_args_list[1][0][0] == 1
    assert commands["target_hum"].call_args_list[2][0][0] == 2
    assert commands["mode"].call_count == 3
    assert commands["mode"].call_args_list[0][0][0] == 0
    assert commands["mode"].call_args_list[1][0][0] == 1
    assert commands["mode"].call_args_list[2][0][0] == 2


async def test_device_reset(hass, data_from_device, test_config_entry):
    """Test device reset identified during coordinator data update."""

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["hum"].reset_mock()
    commands["sav_hum"].reset_mock()
    commands["available"].reset_mock()
    commands["zone"].reset_mock()
    commands["target_hum"].reset_mock()
    commands["mode"].reset_mock()
    commands["cur_hum"].reset_mock()
    commands["uptime"].return_value = -12

    coordinator = hass.data["xbee_humidifier"][test_config_entry.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    commands["bind"].assert_called_once_with()
    assert commands["uptime"].call_count == 2
    assert commands["uptime"].call_args_list[0][0] == ()
    assert (
        abs(
            commands["uptime"].call_args_list[1][0][0]
            + 12
            - dt.datetime.now(tz=dt.timezone.utc).timestamp()
        )
        < 2
    )

    assert commands["sav_hum"].call_count == 0
    assert commands["available"].call_count == 0
    assert commands["zone"].call_count == 0
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == [0, False]
    assert commands["hum"].call_args_list[1][0][0] == [1, False]
    assert commands["hum"].call_args_list[2][0][0] == [2, False]
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == [0, None]
    assert commands["cur_hum"].call_args_list[1][0][0] == [1, None]
    assert commands["cur_hum"].call_args_list[2][0][0] == [2, None]
    assert commands["target_hum"].call_count == 5
    assert commands["target_hum"].call_args_list[0][0][0] == [0, 32]
    assert commands["target_hum"].call_args_list[1][0][0] == [0, 42]
    assert commands["target_hum"].call_args_list[2][0][0] == [1, 32]
    assert commands["target_hum"].call_args_list[3][0][0] == [1, 42]
    assert commands["target_hum"].call_args_list[4][0][0] == [2, 42]
    assert commands["mode"].call_count == 5
    assert commands["mode"].call_args_list[0][0][0] == [0, "away"]
    assert commands["mode"].call_args_list[1][0][0] == [0, "normal"]
    assert commands["mode"].call_args_list[2][0][0] == [1, "away"]
    assert commands["mode"].call_args_list[3][0][0] == [1, "normal"]
    assert commands["mode"].call_args_list[4][0][0] == [2, "normal"]


async def test_connection_recovery(hass, data_from_device, test_config_entry):
    """Test device coming back online after being unavailable during last update."""

    commands["bind"].reset_mock()
    commands["uptime"].reset_mock()
    commands["hum"].reset_mock()
    commands["sav_hum"].reset_mock()
    commands["available"].reset_mock()
    commands["zone"].reset_mock()
    commands["target_hum"].reset_mock()
    commands["mode"].reset_mock()
    commands["cur_hum"].reset_mock()

    coordinator = hass.data["xbee_humidifier"][test_config_entry.entry_id]
    coordinator.last_update_success = False
    data_from_device(hass, IEEE, {"pressure_in": 3963})
    await hass.async_block_till_done()

    commands["bind"].assert_called_once_with()
    commands["uptime"].assert_called_once_with()
    assert commands["sav_hum"].call_count == 3
    assert commands["sav_hum"].call_args_list[0][0][0] == 0
    assert commands["sav_hum"].call_args_list[1][0][0] == 1
    assert commands["sav_hum"].call_args_list[2][0][0] == 2
    assert commands["available"].call_count == 3
    assert commands["available"].call_args_list[0][0][0] == 0
    assert commands["available"].call_args_list[1][0][0] == 1
    assert commands["available"].call_args_list[2][0][0] == 2
    assert commands["zone"].call_count == 3
    assert commands["zone"].call_args_list[0][0][0] == 0
    assert commands["zone"].call_args_list[1][0][0] == 1
    assert commands["zone"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_count == 3
    assert commands["hum"].call_args_list[0][0][0] == 0
    assert commands["hum"].call_args_list[1][0][0] == 1
    assert commands["hum"].call_args_list[2][0][0] == 2
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == 0
    assert commands["cur_hum"].call_args_list[1][0][0] == 1
    assert commands["cur_hum"].call_args_list[2][0][0] == 2
    assert commands["target_hum"].call_count == 3
    assert commands["target_hum"].call_args_list[0][0][0] == 0
    assert commands["target_hum"].call_args_list[1][0][0] == 1
    assert commands["target_hum"].call_args_list[2][0][0] == 2
    assert commands["mode"].call_count == 3
    assert commands["mode"].call_args_list[0][0][0] == 0
    assert commands["mode"].call_args_list[1][0][0] == 1
    assert commands["mode"].call_args_list[2][0][0] == 2
