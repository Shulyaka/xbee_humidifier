"""Test config."""

import config
from lib.core import Entity


def test_config():
    """Test config."""
    assert isinstance(config.debug, bool)
    assert isinstance(config.pump, Entity)
    assert isinstance(config.pump_temp, Entity)
    assert isinstance(config.pressure_in, Entity)
    assert isinstance(config.pressure_out, Entity)
    assert isinstance(config.valve_switch, dict)
    assert len(config.valve_switch) == 4
    for x in range(4):
        assert isinstance(config.valve_switch[x], Entity)
