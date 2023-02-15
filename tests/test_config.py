"""Test config."""

import config
from lib.core import Sensor


def test_config():
    """Test config."""
    assert isinstance(config.debug, bool)
    assert isinstance(config.pump, Sensor)
    assert isinstance(config.pump_temp, Sensor)
    assert isinstance(config.pressure_in, Sensor)
    assert isinstance(config.pressure_out, Sensor)
    assert isinstance(config.valve_switch, dict)
    assert len(config.valve_switch) == 4
    for x in range(4):
        assert isinstance(config.valve_switch[x], Sensor)
