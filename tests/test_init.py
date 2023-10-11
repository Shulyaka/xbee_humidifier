"""Test __init__."""

from commands import HumidifierCommands
from dutycycle import DutyCycle
from humidifier import GenericHygrostat
from lib.core import Sensor
from lib.mainloop import main_loop

import flash


def test_init():
    """Test the main code."""
    assert flash._setup is None
    assert isinstance(flash._zone, dict)
    assert len(flash._zone) == 3
    assert isinstance(flash._sensor, dict)
    assert len(flash._sensor) == 3
    assert isinstance(flash._available, dict)
    assert len(flash._available) == 3
    assert isinstance(flash._humidifier, dict)
    assert len(flash._humidifier) == 3

    for x in range(3):
        assert isinstance(flash._zone[x], Sensor)
        assert isinstance(flash._sensor[x], Sensor)
        assert isinstance(flash._available[x], Sensor)
        assert isinstance(flash._humidifier[x], GenericHygrostat)

    assert isinstance(flash._pump_block, Sensor)
    assert isinstance(flash._duty_cycle, DutyCycle)
    assert isinstance(flash._commands, HumidifierCommands)

    assert len(flash._warning_subscribers) == 3
    flash._sensor[2].state = 55
    main_loop.run_once()
    assert flash._warning_subscribers is None
    assert flash._warning_cb is None
