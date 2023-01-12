"""Test tosr lib."""

import sys
from unittest.mock import MagicMock, PropertyMock, patch

sys.path.append("tests/modules")
sys.path.append("flash/lib")
sys.modules["time"] = __import__("mock_time")

from time import ticks_ms as mock_ticks_ms  # noqa: E402

from mainloop import main_loop  # noqa: E402

with patch("flash.lib.tosr0x.stdout.buffer.write") as mock_stdout:
    with patch("flash.lib.tosr0x.stdin.buffer.read") as mock_stdin:
        from flash.lib.tosr import TosrTemp, tosr_switch, tosr_temp

        assert mock_stdout.call_count == 2
        assert mock_stdout.call_args_list[0].args == "n"
        assert mock_stdout.call_args_list[1].args == "["
        assert mock_stdin.call_count == 2


@patch("flash.lib.tosr.tosr")
def test_tosr_switch(mock_tosr):
    """Test TosrSwitch class."""
    mock_ticks_ms.return_value = 1000
    mock_tosr.get_relay_state.return_value = True
    assert tosr_switch[0].state

    mock_tosr.get_relay_state.return_value = False
    assert not tosr_switch[0].state

    mock_tosr.get_relay_state.reset_mock()
    mock_ticks_ms.return_value = 31000
    main_loop.run_once()
    assert not tosr_switch[0].state
    mock_tosr.get_relay_state.assert_called_once()

    mock_tosr.get_relay_state.reset_mock()
    callback = MagicMock()
    tosr_switch[1].subscribe(callback)
    mock_ticks_ms.return_value = 61000
    main_loop.run_once()
    mock_tosr.get_relay_state.assert_called_once()
    assert callback.call_count == 0

    mock_tosr.get_relay_state.reset_mock()
    mock_tosr.get_relay_state.return_value = True
    mock_ticks_ms.return_value = 91000
    main_loop.run_once()
    mock_tosr.get_relay_state.assert_called_once()
    callback.assert_called_once(True)


@patch("flash.lib.tosr.tosr")
def test_tosr_temp(mock_tosr):
    """Test TosrTemp class."""
    mock_ticks_ms.return_value = 1000
    mock_temperature = PropertyMock(return_value=0)
    type(mock_tosr).temperature = mock_temperature
    mock_temperature.return_value = 42
    tosr_temp.update()
    assert tosr_temp.state == 42

    sensor = TosrTemp(period=500, threshold=5)

    # Set up the test
    mock_temperature.reset_mock()
    mock_temperature.return_value = 10
    callback = MagicMock()
    sensor.subscribe(callback)

    # Test that sensor is not read too often
    main_loop.run_once()
    assert callback.call_count == 0
    assert mock_temperature.call_count == 0

    # Test that sensor is read after 500 ms
    mock_ticks_ms.return_value = 1500
    main_loop.run_once()
    callback.assert_called_once_with(10)
    assert sensor.state == 10
    mock_temperature.assert_called_once_with()

    # Test that callback is called if the change is above threshold
    callback.reset_mock()
    mock_temperature.reset_mock()
    mock_temperature.return_value = 15
    mock_ticks_ms.return_value = 2000
    main_loop.run_once()
    callback.assert_called_once_with(15)
    assert sensor.state == 15
    mock_temperature.assert_called_once_with()

    # Test that callback is not called if the change is below threshold but state returns the correct value
    callback.reset_mock()
    mock_temperature.reset_mock()
    mock_temperature.return_value = 15.0625
    mock_ticks_ms.return_value = 2500
    main_loop.run_once()
    assert callback.call_count == 0
    assert sensor.state == 15.0625
    mock_temperature.assert_called_once_with()

    # Test that threshold is ignored on manual update
    mock_temperature.reset_mock()
    sensor.update()
    callback.assert_called_once_with(15.0625)
    assert sensor.state == 15.0625
    mock_temperature.assert_called_once_with()
