"""Test xbee_humidifier."""
from .conftest import commands
from .const import IEEE


def test_init(hass, caplog, data_from_device, test_config_entry):
    """Test humidifier services."""

    assert len(commands) == 12
    commands["bind"].assert_called_once_with()
    commands["unique_id"].assert_called_once_with()
    commands["atcmd"].assert_called_once_with("VL")
    commands["pump"].assert_called_once_with()
    commands["pump_temp"].assert_called_once_with()
    commands["pump_block"].assert_called_once_with()
    commands["pressure_in"].assert_called_once_with()
    commands["fan"].assert_called_once_with()
    commands["aux_led"].assert_called_once_with()
    commands["pump_speed"].assert_called_once_with()
    assert commands["valve"].call_count == 4
    assert commands["valve"].call_args_list[0][0][0] == 0
    assert commands["valve"].call_args_list[1][0][0] == 1
    assert commands["valve"].call_args_list[2][0][0] == 2
    assert commands["valve"].call_args_list[3][0][0] == 3
    assert commands["hum"].call_count == 18
    assert commands["hum"].call_args_list[0][0][0] == 0
    assert commands["hum"].call_args_list[1][0][0] == 1
    assert commands["hum"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_args_list[3][0][0] == [[0], {"mode": "away"}]
    assert commands["hum"].call_args_list[4][0][0] == [[1], {"mode": "away"}]
    assert commands["hum"].call_args_list[5][0][0] == [[2], {"mode": "away"}]
    assert commands["hum"].call_args_list[6][0][0] == [[0], {"hum": 32}]
    assert commands["hum"].call_args_list[7][0][0] == [[1], {"hum": 32}]
    assert commands["hum"].call_args_list[8][0][0] == [[2], {"hum": 32}]
    assert commands["hum"].call_args_list[9][0][0] == [[0], {"mode": "normal"}]
    assert commands["hum"].call_args_list[10][0][0] == [[1], {"mode": "normal"}]
    assert commands["hum"].call_args_list[11][0][0] == [[2], {"mode": "normal"}]
    assert commands["hum"].call_args_list[12][0][0] == [[0], {"hum": 42}]
    assert commands["hum"].call_args_list[13][0][0] == [[1], {"hum": 42}]
    assert commands["hum"].call_args_list[14][0][0] == [[2], {"hum": 42}]
    assert commands["hum"].call_args_list[15][0][0] == [[0], {"is_on": False}]
    assert commands["hum"].call_args_list[16][0][0] == [[1], {"is_on": False}]
    assert commands["hum"].call_args_list[17][0][0] == [[2], {"is_on": False}]

    data_from_device(hass, IEEE, {"log": {"msg": "Test log", "sev": 20}})
    assert "Test log" in caplog.text


async def test_refresh(hass, caplog, data_from_device, test_config_entry):
    """Test config entry reload."""

    commands["bind"].reset_mock()
    commands["hum"].reset_mock()
    data_from_device(hass, IEEE, {"log": {"msg": "Not initialized", "sev": 20}})
    await hass.async_block_till_done()
    commands["bind"].assert_called_once_with()
    assert commands["hum"].call_count == 18
    assert commands["hum"].call_args_list[0][0][0] == 0
    assert commands["hum"].call_args_list[1][0][0] == 1
    assert commands["hum"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_args_list[3][0][0] == [[0], {"mode": "away"}]
    assert commands["hum"].call_args_list[4][0][0] == [[0], {"hum": 32}]
    assert commands["hum"].call_args_list[5][0][0] == [[0], {"mode": "normal"}]
    assert commands["hum"].call_args_list[6][0][0] == [[0], {"hum": 42}]
    assert commands["hum"].call_args_list[7][0][0] == [[0], {"is_on": False}]
    assert commands["hum"].call_args_list[8][0][0] == [[1], {"mode": "away"}]
    assert commands["hum"].call_args_list[9][0][0] == [[1], {"hum": 32}]
    assert commands["hum"].call_args_list[10][0][0] == [[1], {"mode": "normal"}]
    assert commands["hum"].call_args_list[11][0][0] == [[1], {"hum": 42}]
    assert commands["hum"].call_args_list[12][0][0] == [[1], {"is_on": False}]
    assert commands["hum"].call_args_list[13][0][0] == [[2], {"mode": "away"}]
    assert commands["hum"].call_args_list[14][0][0] == [[2], {"hum": 32}]
    assert commands["hum"].call_args_list[15][0][0] == [[2], {"mode": "normal"}]
    assert commands["hum"].call_args_list[16][0][0] == [[2], {"hum": 42}]
    assert commands["hum"].call_args_list[17][0][0] == [[2], {"is_on": False}]


def test_reload(hass, caplog, data_from_device, test_config_entry):
    """Test config entry reload."""

    new_data = test_config_entry.data.copy()
    new_data["humidifier_0"] = test_config_entry.data["humidifier_0"].copy()
    new_data["humidifier_0"]["target_sensor"] = "sensor.test4"

    assert test_config_entry.data != new_data
    assert hass.config_entries.async_update_entry(test_config_entry, data=new_data)
