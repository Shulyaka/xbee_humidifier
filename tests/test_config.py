"""Test config."""

import config
from lib.core import Sensor


def test_config():
    """Test config."""
    assert isinstance(config.debug, bool)
    assert isinstance(config.pump, Sensor)
    assert config.pump._type is bool
    assert isinstance(config.pump_temp, Sensor)
    assert config.pump_temp._type is None
    assert isinstance(config.pressure_in, Sensor)
    assert config.pressure_in._type is None
    assert isinstance(config.pressure_out, Sensor)
    assert config.pressure_out._type is None
    assert isinstance(config.water_temperature, Sensor)
    assert config.water_temperature._type is None
    assert isinstance(config.aux_din, Sensor)
    assert config.aux_din._type is bool
    assert isinstance(config.aux_led, Sensor)
    assert config.aux_led._type is bool
    assert isinstance(config.pump_speed, Sensor)
    assert config.pump_speed._type is None
    assert isinstance(config.fan, Sensor)
    assert config.fan._type is bool
    assert isinstance(config.valve_switch, dict)
    assert len(config.valve_switch) == 4
    for x in range(4):
        assert isinstance(config.valve_switch[x], Sensor)
        assert config.valve_switch[x]._type is bool
