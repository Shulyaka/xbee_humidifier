"""Test xbee_humidifier."""
from homeassistant.components.humidifier import DOMAIN as HUMIDIFIER, SERVICE_SET_MODE
from homeassistant.const import ATTR_ENTITY_ID, ATTR_MODE

from .conftest import commands
from .const import IEEE

ENTITY = "humidifier.xbee_humidifier_2_humidifier"


def test_init(hass, caplog, data_from_device, test_config_entry):
    """Test component initialization."""

    assert len(commands) == 16
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
    assert commands["cur_hum"].call_count == 3
    assert commands["cur_hum"].call_args_list[0][0][0] == 0
    assert commands["cur_hum"].call_args_list[1][0][0] == 1
    assert commands["cur_hum"].call_args_list[2][0][0] == 2
    assert commands["target_hum"].call_count == 8
    assert commands["target_hum"].call_args_list[0][0][0] == 0
    assert commands["target_hum"].call_args_list[1][0][0] == 1
    assert commands["target_hum"].call_args_list[2][0][0] == 2
    assert commands["target_hum"].call_args_list[3][0][0] == [0, 32]
    assert commands["target_hum"].call_args_list[4][0][0] == [1, 32]
    assert commands["target_hum"].call_args_list[5][0][0] == [2, 42]
    assert commands["target_hum"].call_args_list[6][0][0] == [0, 42]
    assert commands["target_hum"].call_args_list[7][0][0] == [1, 42]
    assert commands["mode"].call_count == 8
    assert commands["mode"].call_args_list[0][0][0] == 0
    assert commands["mode"].call_args_list[1][0][0] == 1
    assert commands["mode"].call_args_list[2][0][0] == 2
    assert commands["mode"].call_args_list[3][0][0] == [0, "away"]
    assert commands["mode"].call_args_list[4][0][0] == [1, "away"]
    assert commands["mode"].call_args_list[5][0][0] == [2, "normal"]
    assert commands["mode"].call_args_list[6][0][0] == [0, "normal"]
    assert commands["mode"].call_args_list[7][0][0] == [1, "normal"]
    assert commands["hum_attr"].call_count == 3
    assert commands["hum_attr"].call_args_list[0][0][0] == 0
    assert commands["hum_attr"].call_args_list[1][0][0] == 1
    assert commands["hum_attr"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_count == 6
    assert commands["hum"].call_args_list[0][0][0] == 0
    assert commands["hum"].call_args_list[1][0][0] == 1
    assert commands["hum"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_args_list[3][0][0] == [2, False]
    assert commands["hum"].call_args_list[4][0][0] == [0, False]
    assert commands["hum"].call_args_list[5][0][0] == [1, False]

    data_from_device(hass, IEEE, {"log": {"msg": "Test log", "sev": 20}})
    assert "Test log" in caplog.text


async def test_refresh(hass, caplog, data_from_device, test_config_entry):
    """Test reinitialize on device reset."""

    data_from_device(hass, IEEE, {"available_1": True})
    await hass.async_block_till_done()

    commands["mode"].return_value = "OK"
    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_SET_MODE,
        service_data={ATTR_ENTITY_ID: ENTITY, ATTR_MODE: "away"},
        blocking=True,
    )

    commands["bind"].reset_mock()
    commands["hum"].reset_mock()
    commands["hum_attr"].reset_mock()
    commands["target_hum"].reset_mock()
    commands["mode"].reset_mock()
    commands["mode"].return_value = "normal"
    data_from_device(hass, IEEE, {"log": {"msg": "Not initialized", "sev": 20}})
    await hass.async_block_till_done()
    commands["bind"].assert_called_once_with()
    assert commands["mode"].call_count == 8
    assert commands["mode"].call_args_list[0][0][0] == 0
    assert commands["mode"].call_args_list[1][0][0] == 1
    assert commands["mode"].call_args_list[2][0][0] == 2
    assert commands["mode"].call_args_list[3][0][0] == [2, "normal"]
    assert commands["mode"].call_args_list[4][0][0] == [0, "away"]
    assert commands["mode"].call_args_list[5][0][0] == [0, "normal"]
    assert commands["mode"].call_args_list[6][0][0] == [1, "normal"]
    assert commands["mode"].call_args_list[7][0][0] == [1, "away"]
    assert commands["target_hum"].call_count == 8
    assert commands["target_hum"].call_args_list[0][0][0] == 0
    assert commands["target_hum"].call_args_list[1][0][0] == 1
    assert commands["target_hum"].call_args_list[2][0][0] == 2
    assert commands["target_hum"].call_args_list[3][0][0] == [2, 42]
    assert commands["target_hum"].call_args_list[4][0][0] == [0, 32]
    assert commands["target_hum"].call_args_list[5][0][0] == [0, 42]
    assert commands["target_hum"].call_args_list[6][0][0] == [1, 42]
    assert commands["target_hum"].call_args_list[7][0][0] == [1, 32]
    assert commands["hum_attr"].call_count == 3
    assert commands["hum_attr"].call_args_list[0][0][0] == 0
    assert commands["hum_attr"].call_args_list[1][0][0] == 1
    assert commands["hum_attr"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_count == 6
    assert commands["hum"].call_args_list[0][0][0] == 0
    assert commands["hum"].call_args_list[1][0][0] == 1
    assert commands["hum"].call_args_list[2][0][0] == 2
    assert commands["hum"].call_args_list[3][0][0] == [2, False]
    assert commands["hum"].call_args_list[4][0][0] == [0, False]
    assert commands["hum"].call_args_list[5][0][0] == [1, False]


async def test_reload(hass, caplog, data_from_device, test_config_entry):
    """Test config entry reload."""

    commands["bind"].reset_mock()
    commands["hum"].reset_mock()
    commands["hum_attr"].reset_mock()
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
    assert commands["hum_attr"].call_count == 3
    assert commands["hum_attr"].call_args_list[0][0][0] == 0
    assert commands["hum_attr"].call_args_list[1][0][0] == 1
    assert commands["hum_attr"].call_args_list[2][0][0] == 2
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
