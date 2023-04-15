"""Test __main__."""

from dutycycle import DutyCycle
from lib.core import Sensor
from lib.humidifier import GenericHygrostat
from lib.mainloop import main_loop

import flash


def test_init():
    """Test the main code."""
    assert isinstance(flash.zone, dict)
    assert len(flash.zone) == 3
    assert isinstance(flash.sensor, dict)
    assert len(flash.sensor) == 3
    assert isinstance(flash.available, dict)
    assert len(flash.available) == 3
    assert isinstance(flash.humidifier, dict)
    assert len(flash.humidifier) == 3

    for x in range(3):
        assert isinstance(flash.zone[x], Sensor)
        assert isinstance(flash.sensor[x], Sensor)
        assert isinstance(flash.available[x], Sensor)
        assert isinstance(flash.humidifier[x], GenericHygrostat)

    assert isinstance(flash.pump_block, Sensor)
    assert isinstance(flash.duty_cycle, DutyCycle)

    assert len(flash._unsubscribe_warning) == 3
    flash.sensor[2].state = 55
    main_loop.run_once()
    assert flash._unsubscribe_warning is None
    assert flash._cancel_warning_cb is None
