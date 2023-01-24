"""Test commands."""

from json import loads as json_loads
import logging
from unittest.mock import patch

import commands
from lib.core import VirtualSensor, VirtualSwitch
from lib.humidifier import GenericHygrostat
import pytest
from xbee import receive_callback as mock_receive_callback, transmit as mock_transmit


def test_commands():
    """Test Commands class."""

    mock_receive_callback.reset_mock()

    valve = {x: VirtualSwitch() for x in range(5)}
    pump_temp = VirtualSensor(34.2)

    humidifier_zone = {x: VirtualSwitch() for x in range(3)}
    humidifier_sensor = {x: VirtualSensor() for x in range(3)}
    humidifier_available = {x: VirtualSwitch() for x in range(3)}

    humidifier = {
        x: GenericHygrostat(
            switch_entity_id=humidifier_zone[x],
            sensor_entity_id=humidifier_sensor[x],
            available_sensor_id=humidifier_available[x],
            min_humidity=15,
            max_humidity=100,
            target_humidity=50,
            dry_tolerance=3,
            wet_tolerance=0,
            initial_state=None,
            away_humidity=35,
            sensor_stale_duration=30 * 60,
        )
        for x in range(3)
    }

    pump = VirtualSwitch()
    pump_block = VirtualSwitch()

    commands.register(
        valve=valve,
        pump_temp=pump_temp,
        humidifier=humidifier,
        humidifier_sensor=humidifier_sensor,
        humidifier_available=humidifier_available,
        humidifier_zone=humidifier_zone,
        pump=pump,
        pump_block=pump_block,
    )

    assert mock_receive_callback.call_count == 1
    rx_callback = mock_receive_callback.call_args[0][0]

    def command(cmd, args=None):
        rx_callback(
            {
                "broadcast": False,
                "dest_ep": 232,
                "sender_eui64": b"\x00\x13\xa2\x00A\xa0n`",
                "payload": '{"command": "' + cmd + '"}'
                if args is None
                else '{"command": "' + cmd + '", "args": ' + str(args) + "}",
                "sender_nwk": 0,
                "source_ep": 232,
                "profile": 49413,
                "cluster": 17,
            }
        )
        assert mock_transmit.call_count == 1
        assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
        resp = json_loads(mock_transmit.call_args[0][1])
        mock_transmit.reset_mock()
        if "error" in resp:
            raise RuntimeError(resp["error"])
        return resp["cmd_" + cmd + "_resp"]

    assert command("test") == "args: (), kwargs: {}"
    assert command("test", "true") == "args: (True,), kwargs: {}"
    assert command("test", '{"test": "123"}') == "args: (), kwargs: {'test': '123'}"
    assert command("test", "[1, 2, 3]") == "args: (1, 2, 3), kwargs: {}"
    assert command("help") == [
        "bind",
        "bind_humidifier_available",
        "bind_humidifier_working",
        "bind_pump",
        "bind_pump_temp",
        "bind_valve",
        "get_pump_block",
        "get_pump_temp",
        "get_valve_state",
        "help",
        "humidifier_get_state",
        "humidifier_override_zone",
        "humidifier_set_current_humidity",
        "humidifier_set_humidity",
        "humidifier_set_mode",
        "humidifier_set_state",
        "logger_set_level",
        "logger_set_target",
        "set_pump",
        "set_pump_block",
        "set_valve_state",
        "test",
        "unbind",
        "unbind_humidifier_available",
        "unbind_humidifier_working",
        "unbind_pump",
        "unbind_pump_temp",
        "unbind_valve",
    ]

    assert command("bind") == "OK"
    pump_temp.state = 34.3
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pump_temp": 34.3}'
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    pump_temp.state = 34.4
    assert mock_transmit.call_count == 0
    assert command("unbind") == "OK"

    assert (
        command("bind", '"\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"')
        == "OK"
    )
    pump_temp.state = 34.5
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert mock_transmit.call_args[0][1] == '{"pump_temp": 34.5}'
    mock_transmit.reset_mock()
    assert (
        command("unbind", '"\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"')
        == "OK"
    )
    pump_temp.state = 34.6
    assert mock_transmit.call_count == 0

    assert command("bind_humidifier_available", 0) == "OK"
    humidifier_sensor[0].state = 51.2
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "number": 0,
        "available": True,
    }
    mock_transmit.reset_mock()
    assert command("unbind_humidifier_available", 0) == "OK"

    assert command("bind_humidifier_working", 1) == "OK"
    humidifier_sensor[1].state = 35.7
    humidifier[1].state = True
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "number": 1,
        "working": True,
    }
    mock_transmit.reset_mock()
    assert command("unbind_humidifier_working", 1) == "OK"

    assert command("bind_pump") == "OK"
    pump.state = True
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pump": true}'
    mock_transmit.reset_mock()
    assert command("unbind_pump") == "OK"
    pump.state = False
    assert mock_transmit.call_count == 0

    assert command("bind_valve", 3) == "OK"
    valve[3].state = True
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"valve_3": true}'
    mock_transmit.reset_mock()
    assert command("unbind_valve", 3) == "OK"
    valve[3].state = False
    assert mock_transmit.call_count == 0

    assert command("bind_pump_temp") == "OK"
    pump_temp.state = 34.7
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pump_temp": 34.7}'
    mock_transmit.reset_mock()
    assert command("unbind_pump_temp") == "OK"
    pump_temp.state = 34.8
    assert mock_transmit.call_count == 0

    assert command("get_pump_temp") == 34.8

    assert not command("get_pump_block")
    pump_block.state = True
    assert command("get_pump_block")

    assert command("humidifier_get_state", 2) == {
        "available": False,
        "cap_attr": {
            "max_hum": 100,
            "min_hum": 15,
        },
        "extra_state_attr": {"sav_hum": 35},
        "is_on": False,
        "number": 2,
        "state_attr": {"hum": 50, "mode": "normal"},
        "working": False,
    }
    assert command("humidifier_set_current_humidity", "[2, 45.5]") == "OK"
    assert command("humidifier_set_mode", '{"number": 2, "mode": "away"}') == "OK"
    assert command("humidifier_set_humidity", "[2, 51]") == "OK"
    assert command("humidifier_set_state", '{"number": 2, "state": true}') == "OK"
    assert command("humidifier_get_state", 2) == {
        "available": True,
        "cap_attr": {
            "max_hum": 100,
            "min_hum": 15,
        },
        "extra_state_attr": {"sav_hum": 50},
        "is_on": True,
        "number": 2,
        "state_attr": {"hum": 51, "mode": "away"},
        "working": True,
    }

    assert humidifier_zone[1].state
    assert command("humidifier_override_zone", '{"number": 1, "value": false}') == "OK"
    assert not humidifier_zone[1].state

    assert command("humidifier_set_state", "[2, false]") == "OK"
    assert not humidifier[2].state

    assert logging.getLogger().getEffectiveLevel() == logging.WARNING
    assert command("logger_set_level", logging.DEBUG) == "OK"
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG

    with patch("commands.logging.getLogger") as mock_getLogger:
        assert command("logger_set_target") == "OK"
        assert len(mock_getLogger.mock_calls) == 2
        assert mock_getLogger.mock_calls[0][1] == ()
        assert mock_getLogger.mock_calls[1][0] == "().setTarget"
        assert mock_getLogger.mock_calls[1][1] == (b"\x00\x13\xa2\x00A\xa0n`",)
        mock_getLogger.reset_mock()
        assert (
            command(
                "logger_set_target",
                '"\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"',
            )
            == "OK"
        )
        assert len(mock_getLogger.mock_calls) == 2
        assert mock_getLogger.mock_calls[0][1] == ()
        assert mock_getLogger.mock_calls[1][0] == "().setTarget"
        assert mock_getLogger.mock_calls[1][1] == (b"\x00\x00\x00\x00\x00\x00\x00\x00",)

    assert not pump.state
    assert command("set_pump", "true") == "OK"
    assert pump.state
    assert command("set_pump", "false") == "OK"
    assert not pump.state

    assert pump_block.state
    assert command("set_pump_block", "false") == "OK"
    assert not pump_block.state
    assert command("set_pump_block", "true") == "OK"
    assert pump_block.state

    assert not command("get_valve_state", "0")
    assert command("set_valve_state", "[0, true]") == "OK"
    assert command("get_valve_state", "0")

    with pytest.raises(RuntimeError) as excinfo:
        command("set_pump_block")
    assert (
        "cmd_set_pump_block() missing 1 required positional argument: 'value'"
        in str(excinfo.value)
    )

    with pytest.raises(RuntimeError) as excinfo:
        command("set_pump_block", '{"number": 2}')
    assert "cmd_set_pump_block() got an unexpected keyword argument 'number'" in str(
        excinfo.value
    )

    with pytest.raises(RuntimeError) as excinfo:
        command("set_pump_block", "[1, 2, 3]")
    assert "cmd_set_pump_block() takes 3 positional arguments but 5 were given" in str(
        excinfo.value
    )
