"""Test __main__."""

from dutycycle import DutyCycle
from humidifier import GenericHygrostat
from lib.core import Sensor
from lib.mainloop import main_loop

import flash


def test_init():
    """Test the main code."""
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

    assert len(flash._unsubscribe_warning) == 3
    flash._sensor[2].state = 55
    main_loop.run_once()
    assert flash._unsubscribe_warning is None
    assert flash._cancel_warning_cb is None
