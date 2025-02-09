"""Test commands."""

import logging
from json import loads as json_loads
from time import sleep as mock_sleep
from unittest.mock import patch

import commands
import config
import pytest
from humidifier import Humidifier
from lib.core import Sensor, Switch
from lib.mainloop import main_loop
from machine import reset_cause as mock_reset_cause, soft_reset as mock_soft_reset
from xbee import atcmd as mock_atcmd, receive as mock_receive, transmit as mock_transmit


def test_commands():
    """Test Commands class."""

    assert mock_transmit.call_count == 0
    main_loop.run_once()
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "uptime": 0,
    }
    mock_transmit.reset_mock()

    humidifier_zone = [Switch() for x in range(3)]
    humidifier_sensor = [Sensor() for x in range(3)]
    humidifier_available = [Switch() for x in range(3)]

    humidifier = [
        Humidifier(
            switch=humidifier_zone[x],
            sensor=humidifier_sensor[x],
            available_sensor=humidifier_available[x],
            target_humidity=50,
            dry_tolerance=3,
            wet_tolerance=0,
            away_humidity=35,
            sensor_stale_duration=30 * 60,
        )
        for x in range(3)
    ]

    pump_block = Switch()

    cmnds = commands.HumidifierCommands(
        humidifier=humidifier,
        sensor=humidifier_sensor,
        available=humidifier_available,
        zone=humidifier_zone,
        pump_block=pump_block,
    )

    mock_receive.reset_mock()
    mock_receive.return_value = None
    cmnds.update()
    assert mock_receive.call_count == 1
    assert mock_transmit.call_count == 0

    mock_receive.reset_mock()
    mock_receive.return_value = {
        "broadcast": False,
        "dest_ep": 232,
        "sender_eui64": b"\x00\x13\xa2\x00A\xa0n`",
        "payload": "invalid_json",
        "sender_nwk": 0,
        "source_ep": 232,
        "profile": 49413,
        "cluster": 17,
    }

    with pytest.raises(ValueError) as excinfo:
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
        assert "nonce" in resp
        value = resp[cmd + "_resp"]
        if isinstance(value, dict) and "err" in value:
            raise RuntimeError(value["err"])
        return value

    assert mock_transmit.call_count == 0
    main_loop.run_once()
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "uptime": 0,
    }
    mock_transmit.reset_mock()

    assert command("test") == "args: (), kwargs: {}"
    assert command("test", "true") == "args: (True,), kwargs: {}"
    assert command("test", '{"test": "123"}') == "args: (), kwargs: {'test': '123'}"
    assert command("test", "[1, 2, 3]") == "args: (1, 2, 3), kwargs: {}"
    assert (
        command("test", '[[1], {"test": "23"}]') == "args: (1,), kwargs: {'test': '23'}"
    )
    assert command("help") == [
        "atcmd",
        "aux_led",
        "available",
        "bind",
        "cur_hum",
        "fan",
        "help",
        "hum",
        "logger",
        "mode",
        "pressure_in",
        "pump",
        "pump_block",
        "pump_speed",
        "pump_temp",
        "reset_cause",
        "sav_hum",
        "soft_reset",
        "target_hum",
        "test",
        "unbind",
        "unique_id",
        "uptime",
        "valve",
        "zone",
    ]

    mock_atcmd.reset_mock()
    assert command("bind") == "OK"
    assert command("bind") == "OK"
    assert command("unique_id") == "0102030405060708"
    assert command("atcmd", '"VL"') == "OK"
    mock_atcmd.assert_called_once_with("VL")
    config.pump_temp.state = 34.3
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pump_temp": 34.3}'
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    config.pump_temp.state = 34.4
    assert mock_transmit.call_count == 0
    assert command("unbind") == "OK"

    assert (
        command("bind", '"\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"')
        == "OK"
    )
    config.pump_temp.state = 34.5
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert mock_transmit.call_args[0][1] == '{"pump_temp": 34.5}'
    mock_transmit.reset_mock()
    assert (
        command("unbind", '"\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"')
        == "OK"
    )
    config.pump_temp.state = 34.6
    assert mock_transmit.call_count == 0

    assert command("bind") == "OK"
    config.pressure_in.state = 6.7
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pressure_in": 6.7}'
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    config.pressure_in.state = 8.9
    assert mock_transmit.call_count == 0
    assert command("pressure_in") == 8.9

    assert command("bind") == "OK"
    humidifier_sensor[0].state = 51.2
    assert mock_transmit.call_count == 0
    main_loop.run_once()
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "available_0": True,
    }

    mock_transmit.reset_mock()
    humidifier_sensor[1].state = 35.7
    assert not humidifier_zone[1].state
    humidifier[1].state = True
    assert mock_transmit.call_count == 0
    main_loop.run_once()
    assert mock_transmit.call_count == 2
    assert mock_transmit.call_args_list[0][0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert json_loads(mock_transmit.call_args_list[0][0][1]) == {
        "available_1": True,
    }
    assert mock_transmit.call_args_list[1][0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert json_loads(mock_transmit.call_args_list[1][0][1]) == {
        "working_1": True,
    }

    assert humidifier_zone[1].state
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    humidifier[1].state = False
    main_loop.run_once()
    assert not humidifier_zone[1].state
    humidifier[1].state = True
    main_loop.run_once()
    assert mock_transmit.call_count == 0

    assert command("bind") == "OK"
    config.pump.state = True
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pump": true}'
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    config.pump.state = False
    assert mock_transmit.call_count == 0

    assert command("bind") == "OK"
    config.valve_switch[3].state = True
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"valve_3": true}'
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    config.valve_switch[3].state = False
    assert mock_transmit.call_count == 0

    assert command("bind") == "OK"
    config.pump_temp.state = 34.7
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x13\xa2\x00A\xa0n`"
    assert mock_transmit.call_args[0][1] == '{"pump_temp": 34.7}'
    mock_transmit.reset_mock()
    assert command("unbind") == "OK"
    config.pump_temp.state = 34.8
    assert mock_transmit.call_count == 0

    assert command("pump_temp") == 34.8

    config.pump_speed.state = 314
    assert command("pump_speed") == 314
    assert command("pump_speed", 234) == "OK"
    assert config.pump_speed.state == 234

    config.fan.state = False
    assert not command("fan")
    assert command("fan", "true") == "OK"
    assert config.fan.state

    config.aux_led.state = False
    assert not command("aux_led")
    assert command("aux_led", "true") == "OK"
    assert config.aux_led.state

    assert not command("pump_block")
    pump_block.state = True
    assert command("pump_block")

    assert command("sav_hum", 2) == 35
    assert command("available", 2) is False
    assert command("zone", 2) is False
    assert command("hum", 2) is False
    assert command("target_hum", 2) == 50
    assert command("mode", 2) == "normal"
    assert command("cur_hum", 2) is None
    assert command("cur_hum", '{"number": 2, "state": 45.5}') == "OK"
    assert command("mode", '{"number": 2, "mode": "away"}') == "OK"
    assert command("target_hum", '{"number": 2, "hum": 51}') == "OK"
    assert command("hum", '{"number": 2, "state": true}') == "OK"
    main_loop.run_once()
    assert command("sav_hum", 2) == 50
    assert command("available", 2)
    assert command("zone", 2)
    assert command("hum", 2)
    assert command("target_hum", 2) == 51
    assert command("mode", 2) == "away"
    assert command("cur_hum", 2) == 45.5

    assert command("hum", '{"number": 2, "state": false}') == "OK"

    assert not humidifier[2].state

    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        assert command("logger", logging.WARNING) == "OK"
        assert logging.getLogger().getEffectiveLevel() == logging.WARNING
    else:
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
                '{"target": "\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000\\u0000"}',  # noqa: E501
            )
            == "OK"
        )
        assert len(mock_getLogger.mock_calls) == 2
        assert mock_getLogger.mock_calls[0][1] == ()
        assert mock_getLogger.mock_calls[1][0] == "().setTarget"
        assert mock_getLogger.mock_calls[1][1] == (b"\x00\x00\x00\x00\x00\x00\x00\x00",)

    assert not config.pump.state
    assert command("pump", "true") == "OK"
    assert command("pump")
    assert config.pump.state
    assert command("pump", "false") == "OK"
    assert not command("pump")
    assert not config.pump.state

    assert pump_block.state
    assert command("pump_block", "false") == "OK"
    assert not pump_block.state
    assert command("pump_block", "true") == "OK"
    assert pump_block.state

    assert not command("valve", "0")
    assert command("valve", "[0, true]") == "OK"
    assert command("valve", "0")

    assert command("uptime") == 0.0
    mock_sleep(5)
    assert command("uptime") == -5.0
    mock_sleep(3)
    assert command("uptime", 1700000000) == "OK"
    assert command("uptime") == 1700000000
    mock_sleep(2)
    assert command("uptime") == 1700000000

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
        "cmd_pump_block() takes from 1 to 3 positional arguments but 5 were given"
        in str(excinfo.value)
    )

    with pytest.raises(RuntimeError) as excinfo:
        command("do_magic")
    assert "No such command" in str(excinfo.value)

    mock_soft_reset.reset_mock()
    assert command("soft_reset") == "OK"
    main_loop.run_once()
    mock_soft_reset.assert_called_once_with()

    mock_reset_cause.reset_mock()
    assert command("reset_cause") == 6
    mock_reset_cause.assert_called_once_with()

    mock_transmit.side_effect = OSError("EAGAIN")

    with patch("lib.mainloop.main_loop.schedule_task") as mock_schedule_task:
        command("test")

    mock_schedule_task.assert_called_once()

    mock_transmit.side_effect = None
