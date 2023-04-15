"""Test xbee_humidifier."""
import json
from unittest.mock import MagicMock

from homeassistant.core import callback
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbee_humidifier.const import DOMAIN

from .const import IEEE, MOCK_CONFIG


async def test_init(hass, caplog):
    """Test humidifier services."""

    calls = []
    commands = {}

    def data_from_device(hass, ieee, data):
        hass.bus.async_fire(
            "zha_event",
            {
                "device_ieee": ieee,
                "unique_id": ieee + ":232:0x0008",
                "device_id": "abcdef01234567899876543210fedcba",
                "endpoint_id": 232,
                "cluster_id": 8,
                "command": "receive_data",
                "args": {"data": json.dumps(data)},
            },
        )

    @callback
    def log_call(call):
        """Log service calls."""
        calls.append(call)
        data = json.loads(call.data["params"]["data"])
        cmd = data["cmd"]
        if cmd not in commands:
            commands[cmd] = MagicMock(return_value="OK")
        if "args" in data:
            response = commands[cmd](data["args"])
        else:
            response = commands[cmd]()
        data_from_device(hass, call.data["ieee"], {cmd + "_resp": response})

    hass.services.async_register("zha", "issue_zigbee_cluster_command", log_call)

    hum_resp = {
        "extra_state_attr": {"sav_hum": 35},
        "is_on": False,
        "cur_hum": None,
        "cap_attr": {"min_hum": 15, "max_hum": 80},
        "available": False,
        "working": False,
        "number": 1,
        "state_attr": {"mode": "normal", "hum": 50},
    }
    commands["hum"] = MagicMock(return_value=hum_resp)
    commands["atcmd"] = MagicMock(
        return_value="XBee3-PRO Zigbee 3.0 TH RELE: 1010\rBuild: Aug  2 2022 14:33:22\rHV: 4247\rBootloader: 1B2 Compiler: 8030001\rStack: 6760\rOK\x00"
    )

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")
    await config_entry.async_setup(hass)
    await hass.async_block_till_done()

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

    commands.clear()

    data_from_device(hass, IEEE, {"log": {"msg": "Test log", "sev": 20}})
    await hass.async_block_till_done()
    assert "Test log" in caplog.text

    assert await config_entry.async_unload(hass)
    await hass.async_block_till_done()
