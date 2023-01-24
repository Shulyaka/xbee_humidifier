"""Test __main__."""

from dutycycle import DutyCycle
from lib.core import Entity
from lib.humidifier import GenericHygrostat

import flash


def test_init():
    """Test the main code."""
    assert isinstance(flash.humidifier_zone, dict)
    assert len(flash.humidifier_zone) == 3
    assert isinstance(flash.humidifier_sensor, dict)
    assert len(flash.humidifier_sensor) == 3
    assert isinstance(flash.humidifier_available, dict)
    assert len(flash.humidifier_available) == 3
    assert isinstance(flash.humidifier, dict)
    assert len(flash.humidifier) == 3

    for x in range(3):
        assert isinstance(flash.humidifier_zone[x], Entity)
        assert isinstance(flash.humidifier_sensor[x], Entity)
        assert isinstance(flash.humidifier_available[x], Entity)
        assert isinstance(flash.humidifier[x], GenericHygrostat)

    assert isinstance(flash.pump_block, Entity)
    assert isinstance(flash.duty_cycle, DutyCycle)
