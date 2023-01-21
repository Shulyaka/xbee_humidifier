"""Test __main__."""

from dutycycle import DutyCycle
from lib.core import Entity
from lib.humidifier import GenericHygrostat

import flash


def test_main():
    """Test the main code."""
    assert isinstance(flash.humidifier_switch, dict)
    assert len(flash.humidifier_switch) == 3
    assert isinstance(flash.humidifier_sensor, dict)
    assert len(flash.humidifier_sensor) == 3
    assert isinstance(flash.humidifier_available, dict)
    assert len(flash.humidifier_available) == 3
    assert isinstance(flash.humidifier, dict)
    assert len(flash.humidifier) == 3

    for x in range(3):
        assert isinstance(flash.humidifier_switch[x], Entity)
        assert isinstance(flash.humidifier_sensor[x], Entity)
        assert isinstance(flash.humidifier_available[x], Entity)
        assert isinstance(flash.humidifier[x], GenericHygrostat)

    assert isinstance(flash.pump_block, Entity)
    assert isinstance(flash.duty_cycle, DutyCycle)
