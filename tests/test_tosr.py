"""Test tosr lib."""

from time import sleep_ms
from unittest.mock import MagicMock

from lib.mainloop import main_loop
from lib.tosr0x import mock_temperature, mock_tosr
from tosr import TosrSwitch, TosrTemp, tosr_switch, tosr_temp


def test_tosr_switch():
    """Test TosrSwitch class."""
    mock_tosr.get_relay_state.return_value = True
    tosr_switch[0].update()
    assert tosr_switch[0].state

    mock_tosr.get_relay_state.return_value = False
    tosr_switch[0].update()
    assert not tosr_switch[0].state

    mock_tosr.get_relay_state.reset_mock()
    mock_tosr.update.reset_mock()
    tosr_switch_2 = TosrSwitch(2)
    assert mock_tosr.get_relay_state.call_count == 1
    assert mock_tosr.update.call_count == 1
    sleep_ms(30000)
    main_loop.run_once()
    assert mock_tosr.get_relay_state.call_count == 2
    assert not tosr_switch_2.state
    assert mock_tosr.get_relay_state.call_count == 2
    assert mock_tosr.update.call_count == 2

    mock_tosr.get_relay_state.reset_mock()
    mock_tosr.update.reset_mock()
    callback = MagicMock()
    tosr_switch_2.subscribe(callback)
    sleep_ms(30000)
    main_loop.run_once()
    assert mock_tosr.update.call_count == 1
    assert mock_tosr.get_relay_state.call_count == 1
    assert callback.call_count == 0

    mock_tosr.get_relay_state.reset_mock()
    mock_tosr.update.reset_mock()
    mock_tosr.get_relay_state.return_value = True
    sleep_ms(30000)
    main_loop.run_once()
    assert mock_tosr.update.call_count == 1
    assert mock_tosr.get_relay_state.call_count == 1
    callback.assert_called_once_with(True)


def test_tosr_temp():
    """Test TosrTemp class."""
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
    sleep_ms(500)
    main_loop.run_once()
    callback.assert_called_once_with(10)
    assert sensor.state == 10
    mock_temperature.assert_called_once_with()

    # Test that callback is called if the change is above threshold
    callback.reset_mock()
    mock_temperature.reset_mock()
    mock_temperature.return_value = 15
    sleep_ms(500)
    main_loop.run_once()
    callback.assert_called_once_with(15)
    assert sensor.state == 15
    mock_temperature.assert_called_once_with()

    # Test that callback is not called if the change is below threshold but state returns the correct value
    callback.reset_mock()
    mock_temperature.reset_mock()
    mock_temperature.return_value = 15.0625
    sleep_ms(500)
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
