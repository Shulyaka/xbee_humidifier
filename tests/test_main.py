"""Test __main__."""

from unittest.mock import patch

from core import Entity
from dutycycle import DutyCycle
from humidifier import GenericHygrostat


def test_main():
    """Test the main code."""
    with patch("mainloop.main_loop.run") as mock_mainloop_run:
        from flash import main
    assert mock_mainloop_run.call_count == 1

    assert isinstance(main.humidifier_switch, dict)
    assert len(main.humidifier_switch) == 3
    assert isinstance(main.humidifier_sensor, dict)
    assert len(main.humidifier_sensor) == 3
    assert isinstance(main.humidifier_available, dict)
    assert len(main.humidifier_available) == 3
    assert isinstance(main.humidifier, dict)
    assert len(main.humidifier) == 3

    for x in range(3):
        assert isinstance(main.humidifier_switch[x], Entity)
        assert isinstance(main.humidifier_sensor[x], Entity)
        assert isinstance(main.humidifier_available[x], Entity)
        assert isinstance(main.humidifier[x], GenericHygrostat)

    assert isinstance(main.pump_block, Entity)
    assert isinstance(main.duty_cycle, DutyCycle)
