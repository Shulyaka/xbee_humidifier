"""Test commands."""

from json import loads as json_loads
import logging
from unittest.mock import patch

import commands
from lib.core import VirtualSensor, VirtualSwitch
from lib.humidifier import GenericHygrostat
from lib.mainloop import main_loop
from machine import soft_reset as mock_soft_reset
import pytest
from xbee import receive as mock_receive, transmit as mock_transmit


def test_commands():
    """Test Commands class."""

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

    cmnds = commands.HumidifierCommands(
        valve=valve,
        pump_temp=pump_temp,
        humidifier=humidifier,
        humidifier_sensor=humidifier_sensor,
        humidifier_available=humidifier_available,
        humidifier_zone=humidifier_zone,
        pump=pump,
        pump_block=pump_block,
    )

    mock_receive.reset_mock()
    mock_receive.return_value = None
    cmnds.update()
    assert mock_receive.call_count == 1
    assert mock_transmit.call_count == 0

    def command(cmd, args=None):
        mock_receive.reset_mock()
        mock_receive.return_value = {
            "broadcast": False,
            "dest_ep": 232,
            "sender_eui64": b"\x00\x13\xa2\x00A\xa0n`",
            "payload": '{"cmd": "' + cmd + '"}'
            if args is None
            else '{"cmd": "' + cmd + '", "args": ' + str(args) + "}",
            "sender_nwk": 0,
            "source_ep": 232,
            "profile": 49413,
            "cluster": 17,
        }
        cmnds.update()
        assert mock_receive.call_count == 2
        assert mock_transmit.call_count == 1
        assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
        resp = json_loads(mock_transmit.call_args[0][1])
        mock_transmit.reset_mock()
        value = resp[cmd + "_resp"]
        if isinstance(value, dict) and "err" in value:
            raise RuntimeError(value["err"])
        return value

    assert command("test") == "args: (), kwargs: {}"
    assert command("test", "true") == "args: (True,), kwargs: {}"
    assert command("test", '{"test": "123"}') == "args: (), kwargs: {'test': '123'}"
    assert command("test", "[1, 2, 3]") == "args: (1, 2, 3), kwargs: {}"
    assert (
        command("test", '[[1], {"test": "23"}]') == "args: (1,), kwargs: {'test': '23'}"
    )
    assert command("help") == [
        "bind",
        "help",
        "hum",
        "hum_bind",
        "hum_unbind",
        "logger",
        "pump",
        "pump_bind",
        "pump_block",
        "pump_temp",
        "pump_temp_bind",
        "pump_temp_unbind",
        "pump_unbind",
        "soft_reset",
        "test",
        "unbind",
        "valve",
        "valve_bind",
        "valve_unbind",
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

    assert command("hum_bind", 0) == "OK"
    assert command("hum_bind", 1) == "OK"
    humidifier_sensor[0].state = 51.2
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "available_0": True,
    }

    mock_transmit.reset_mock()
    humidifier_sensor[1].state = 35.7
    assert not humidifier_zone[1].state
    humidifier[1].state = True
    assert humidifier_zone[1].state
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "working_1": True,
    }
    mock_transmit.reset_mock()
    assert command("hum_unbind", 1) == "OK"
    assert command("hum_unbind", 0) == "OK"

    assert command("pump_bind") == "OK"
    pump.state = True
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pump": true}'
    mock_transmit.reset_mock()
    assert command("pump_unbind") == "OK"
    pump.state = False
    assert mock_transmit.call_count == 0

    assert command("valve_bind", 3) == "OK"
    valve[3].state = True
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"valve_3": true}'
    mock_transmit.reset_mock()
    assert command("valve_unbind", 3) == "OK"
    valve[3].state = False
    assert mock_transmit.call_count == 0

    assert command("pump_temp_bind") == "OK"
    pump_temp.state = 34.7
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pump_temp": 34.7}'
    mock_transmit.reset_mock()
    assert command("pump_temp_unbind") == "OK"
    pump_temp.state = 34.8
    assert mock_transmit.call_count == 0

    assert command("pump_temp") == 34.8

    assert not command("pump_block")
    pump_block.state = True
    assert command("pump_block")

    assert command("hum", 2) == {
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
    assert command("hum", '{"number": 2, "cur_hum": 45.5}') == "OK"
    assert command("hum", '{"number": 2, "mode": "away"}') == "OK"
    assert command("hum", '{"number": 2, "hum": 51}') == "OK"
    assert command("hum", '{"number": 2, "is_on": true}') == "OK"
    assert command("hum", 2) == {
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
    assert command("hum", '{"number": 1, "working": false}') == "OK"
    assert not humidifier_zone[1].state

    assert (
        command(
            "hum",
            '{"number": 2, "is_on": false, "cur_hum": 45.5, "mode": "away", "hum": 51}',
        )
        == "OK"
    )
    assert not humidifier[2].state

    assert logging.getLogger().getEffectiveLevel() == logging.WARNING
    assert command("logger", logging.DEBUG) == "OK"
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG

    with patch("lib.core.logging.getLogger") as mock_getLogger:
        assert command("logger") == "OK"
        assert len(mock_getLogger.mock_calls) == 2
        assert mock_getLogger.mock_calls[0][1] == ()
        assert mock_getLogger.mock_calls[1][0] == "().setTarget"
        assert mock_getLogger.mock_calls[1][1] == (b"\x00\x13\xa2\x00A\xa0n`",)
        mock_getLogger.reset_mock()
        assert (
            command(
                "logger",
                '{"target": "\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"}',
            )
            == "OK"
        )
        assert len(mock_getLogger.mock_calls) == 2
        assert mock_getLogger.mock_calls[0][1] == ()
        assert mock_getLogger.mock_calls[1][0] == "().setTarget"
        assert mock_getLogger.mock_calls[1][1] == (b"\x00\x00\x00\x00\x00\x00\x00\x00",)

    assert not pump.state
    assert command("pump", "true") == "OK"
    assert command("pump")
    assert pump.state
    assert command("pump", "false") == "OK"
    assert not command("pump")
    assert not pump.state

    assert pump_block.state
    assert command("pump_block", "false") == "OK"
    assert not pump_block.state
    assert command("pump_block", "true") == "OK"
    assert pump_block.state

    assert not command("valve", "0")
    assert command("valve", "[0, true]") == "OK"
    assert command("valve", "0")

    with pytest.raises(RuntimeError) as excinfo:
        command("valve")
    assert "cmd_valve() missing 1 required positional argument: 'number'" in str(
        excinfo.value
    )

    with pytest.raises(RuntimeError) as excinfo:
        command("pump_block", '{"number": 2}')
    assert "cmd_pump_block() got an unexpected keyword argument 'number'" in str(
        excinfo.value
    )

    with pytest.raises(RuntimeError) as excinfo:
        command("pump_block", "[1, 2, 3]")
    assert (
        "cmd_pump_block() takes from 2 to 3 positional arguments but 5 were given"
        in str(excinfo.value)
    )

    assert command("soft_reset") == "OK"
    main_loop.run_once()
    mock_soft_reset.assert_called_once_with()
