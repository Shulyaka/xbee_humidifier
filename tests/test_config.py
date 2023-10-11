"""Test config."""

import importlib

import config
from lib.core import Sensor, Switch
from lib.xbeepin import AnalogInput, AnalogOutput, DigitalInput, DigitalOutput
from tosr import TosrSwitch, TosrTemp
from tosr0x import tosr0x_version as mock_tosr0x_version


def _test_config_base(config):
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


def test_config_production():
    """Test config."""
    mock_tosr0x_version.return_value = 10
    mock_tosr0x_version.reset_mock()
    importlib.reload(config)
    mock_tosr0x_version.assert_called_once_with()
    assert not config.debug
    _test_config_base(config)
    assert isinstance(config.pump, DigitalOutput)
    assert isinstance(config.pump_temp, TosrTemp)
    assert isinstance(config.pressure_in, AnalogInput)
    assert isinstance(config.pressure_out, AnalogInput)
    assert isinstance(config.water_temperature, AnalogInput)
    assert isinstance(config.aux_din, DigitalInput)
    assert isinstance(config.aux_led, DigitalOutput)
    assert isinstance(config.pump_speed, AnalogOutput)
    assert isinstance(config.fan, DigitalOutput)
    for x in range(4):
        assert isinstance(config.valve_switch[x], TosrSwitch)


def test_config_simulation():
    """Test config."""
    mock_tosr0x_version.return_value = None
    mock_tosr0x_version.reset_mock()
    importlib.reload(config)
    mock_tosr0x_version.assert_called_once_with()
    assert config.debug
    _test_config_base(config)
    assert isinstance(config.pump, Switch)
    assert isinstance(config.aux_din, Switch)
    assert isinstance(config.aux_led, Switch)
    assert isinstance(config.fan, Switch)
    for x in range(4):
        assert isinstance(config.valve_switch[x], Switch)
