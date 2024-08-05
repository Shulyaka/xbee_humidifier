"""Test xbeepin lib."""

from time import sleep_ms
from unittest import mock

from lib import xbeepin
from lib.mainloop import main_loop
from machine import ADC as mock_ADC, PWM as mock_PWM, Pin as mock_Pin


def test_digital_output():
    """Test DigitalOutput class."""
    main_loop.reset()
    mock_Pin.init.reset_mock()

    switch = xbeepin.DigitalOutput("D0")
    mock_Pin.init.assert_called_once_with("D0", mock_Pin.OUT)

    # Test read true value
    switch._pin.value.reset_mock()
    switch._pin.value.return_value = True
    assert switch.state
    switch._pin.value.assert_called_once_with()

    # Test read false value
    switch._pin.value.reset_mock()
    switch._pin.value.return_value = False
    assert not switch.state
    switch._pin.value.assert_called_once_with()

    # Test write true value
    switch._pin.value.reset_mock()
    callback = mock.MagicMock()
    switch.subscribe(callback)
    switch.state = True
    switch._pin.value.assert_called_once_with(True)
    callback.assert_called_once_with(True)

    # Test write false value
    switch._pin.value.reset_mock()
    callback.reset_mock()
    switch.state = False
    switch._pin.value.assert_called_once_with(False)
    callback.assert_called_once_with(False)


def test_digital_input():
    """Test DigitalInput class."""
    main_loop.reset()
    mock_Pin.init.reset_mock()

    binary_sensor = xbeepin.DigitalInput("D0")
    mock_Pin.init.assert_called_once_with("D0", mock_Pin.IN, mock_Pin.PULL_UP)

    # Set up the test
    binary_sensor._pin.value.reset_mock()
    binary_sensor._pin.value.return_value = False
    callback = mock.MagicMock()
    binary_sensor.subscribe(callback)

    # Test that sensor is not read too often
    main_loop.run_once()
    assert callback.call_count == 0
    assert binary_sensor._pin.value.call_count == 0

    # Test that sensor is read after 500 ms
    sleep_ms(500)
    main_loop.run_once()
    assert callback.call_count == 0
    assert not binary_sensor.state
    binary_sensor._pin.value.assert_called_once_with()

    # Test repeated read
    binary_sensor._pin.value.reset_mock()
    binary_sensor._pin.value.return_value = True
    sleep_ms(500)
    main_loop.run_once()
    callback.assert_called_once_with(True)
    assert binary_sensor.state
    binary_sensor._pin.value.assert_called_once_with()


def test_analog_output():
    """Test AnalogOutput class."""
    main_loop.reset()
    mock_PWM.init.reset_mock()

    number = xbeepin.AnalogOutput("D0")
    mock_PWM.init.assert_called_once_with("D0")

    # Test initial write
    number._pin.duty.reset_mock()
    number._pin.duty.return_value = 10
    assert number.state == 10
    number._pin.duty.assert_called_once_with()

    # Test change value
    number._pin.duty.reset_mock()
    number._pin.duty.return_value = 20
    assert number.state == 20
    number._pin.duty.assert_called_once_with()

    # Test callback
    number._pin.duty.reset_mock()
    callback = mock.MagicMock()
    number.subscribe(callback)
    number.state = 30
    number._pin.duty.assert_called_once_with(30)
    callback.assert_called_once_with(30)


def test_analog_input():
    """Test AnalogInput class."""
    main_loop.reset()
    mock_ADC.init.reset_mock()

    sensor = xbeepin.AnalogInput("D0", lowpass=2500)
    mock_ADC.init.assert_called_once_with("D0")

    # Set up the test
    sensor._pin.read.reset_mock()
    sensor._pin.read.return_value = 10
    callback = mock.MagicMock()
    sensor.subscribe(callback)

    # Test that sensor is not read too often
    main_loop.run_once()
    assert callback.call_count == 0
    assert sensor._pin.read.call_count == 0

    # Test that sensor is read after 500 ms
    sleep_ms(500)
    main_loop.run_once()
    callback.assert_called_once_with(10)
    assert sensor.state == 10
    sensor._pin.read.assert_called_once_with()

    # Test that callback is called if the change is above lowpass threshold
    callback.reset_mock()
    sensor._pin.read.reset_mock()
    sensor._pin.read.return_value = 15
    sleep_ms(500)
    main_loop.run_once()
    callback.assert_called_once_with(15)
    assert sensor.state == 15
    sensor._pin.read.assert_called_once_with()

    # Test that callback is not called if the change is below the lowpass threshold
    # but state returns the correct value
    callback.reset_mock()
    sensor._pin.read.reset_mock()
    sensor._pin.read.return_value = 19
    sleep_ms(500)
    main_loop.run_once()
    assert callback.call_count == 0
    assert sensor.state == 19
    sensor._pin.read.assert_called_once_with()

    # Test that the lowpass threshold is ignored on manual update
    sensor._pin.read.reset_mock()
    sensor.update()
    callback.assert_called_once_with(19)
    assert sensor.state == 19
    sensor._pin.read.assert_called_once_with()
