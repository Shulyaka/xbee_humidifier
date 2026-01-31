"""The tests for the Humidifier class."""

from time import sleep as mock_sleep
from unittest.mock import MagicMock

import pytest
from humidifier import _MODE_AWAY as MODE_AWAY, _MODE_NORMAL as MODE_NORMAL, Humidifier
from lib.core import Sensor, Switch
from lib.mainloop import main_loop

TARGET_HUMIDITY = 42

humidifier_switch = Switch()
humidifier_sensor = Sensor()

calls = []
switch_unsubscribe = humidifier_switch.subscribe(lambda x: calls.append(x))


def test_humidifier():
    """Test Humidifier class."""
    humidifier_available = Switch()
    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=humidifier_available,
        target_humidity=50,
        dry_tolerance=3,
        wet_tolerance=0,
        away_humidity=35,
        sensor_stale_duration=30 * 60,
    )

    assert isinstance(humidifier, Switch)

    callback = MagicMock()
    humidifier.subscribe(callback)

    assert not humidifier_available.state

    humidifier_sensor.state = 40
    main_loop.run_once()
    assert humidifier_available.state
    assert not humidifier.state

    humidifier.state = True
    main_loop.run_once()
    assert humidifier.state
    assert humidifier_switch.state
    callback.assert_called_once_with(True)

    callback.reset_mock()
    humidifier.state = False
    main_loop.run_once()
    assert not humidifier.state
    assert not humidifier_switch.state
    callback.assert_called_once_with(False)


def test_humidifier_switch():
    """Test humidifier switching test switch."""
    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=Switch(),
    )
    humidifier.state = True

    assert not humidifier_switch.state

    _setup_sensor(23)

    humidifier.humidity = 32
    main_loop.run_once()

    assert humidifier_switch.state
    humidifier.state = False
    main_loop.run_once()


def _setup_sensor(humidity):
    """Set up the test sensor."""
    humidifier_sensor.state = humidity


@pytest.fixture
def setup_comp_2():
    """Initialize components."""
    _setup_sensor(45)

    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=Switch(),
        dry_tolerance=2,
        wet_tolerance=4,
        away_humidity=35,
    )
    humidifier.state = True
    yield humidifier
    humidifier.state = False
    main_loop.run_once()


def test_unavailable_state():
    """Test the setting of defaults to unknown."""
    _setup_sensor("unavailable")
    humidifier_available = Switch()
    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=humidifier_available,
        dry_tolerance=2,
        wet_tolerance=4,
        away_humidity=35,
    )
    # The target sensor is unavailable, that should propagate to the humidifier entity:
    assert not humidifier_available.state

    # Sensor online
    _setup_sensor(30)
    main_loop.run_once()
    assert humidifier_available.state
    assert not humidifier.state


def test_default_setup_params(setup_comp_2):
    """Test the setup with default parameters."""
    humidifier = setup_comp_2
    assert humidifier._target_humidity == 50


def test_set_target_humidity(setup_comp_2):
    """Test the setting of the target humidity."""
    humidifier = setup_comp_2
    humidifier.humidity = 40
    assert humidifier._target_humidity == 40
    with pytest.raises(TypeError):
        humidifier.humidity = None
    with pytest.raises(ValueError):
        humidifier.humidity = "str"
    assert humidifier._target_humidity == 40


def test_set_away_mode(setup_comp_2):
    """Test the setting away mode."""
    humidifier = setup_comp_2
    humidifier.humidity = 44
    humidifier.mode = MODE_AWAY
    assert humidifier._target_humidity == 35


def test_set_away_mode_and_restore_prev_humidity(setup_comp_2):
    """Test the setting and removing away mode.

    Verify original humidity is restored.
    """
    humidifier = setup_comp_2
    humidifier.humidity = 44
    humidifier.mode = MODE_AWAY
    assert humidifier._target_humidity == 35
    humidifier.mode = MODE_NORMAL
    assert humidifier._target_humidity == 44


def test_set_away_mode_twice_and_restore_prev_humidity(setup_comp_2):
    """Test the setting away mode twice in a row.

    Verify original humidity is restored.
    """
    humidifier = setup_comp_2
    humidifier.humidity = 44
    humidifier.mode = MODE_AWAY
    humidifier.mode = MODE_AWAY
    assert humidifier._target_humidity == 35
    humidifier.mode = MODE_NORMAL
    assert humidifier._target_humidity == 44


def test_set_target_humidity_humidifier_on(setup_comp_2):
    """Test if target humidity turn humidifier on."""
    humidifier = setup_comp_2
    _setup_switch(False)
    _setup_sensor(36)
    humidifier.humidity = 45
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert call


def test_set_target_humidity_humidifier_off(setup_comp_2):
    """Test if target humidity turn humidifier off."""
    humidifier = setup_comp_2
    _setup_switch(True)
    _setup_sensor(45)
    humidifier.humidity = 36
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert not call


def test_humidity_change_humidifier_on_within_tolerance(setup_comp_2):
    """Test if humidity change doesn't turn on within tolerance."""
    humidifier = setup_comp_2
    _setup_switch(False)
    humidifier.humidity = 44
    main_loop.run_once()
    _setup_sensor(43)
    main_loop.run_once()
    assert len(calls) == 0


def test_humidity_change_humidifier_on_outside_tolerance(setup_comp_2):
    """Test if humidity change turn humidifier on outside dry tolerance."""
    humidifier = setup_comp_2
    _setup_switch(False)
    humidifier.humidity = 44
    _setup_sensor(42)
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert call


def test_humidity_change_humidifier_off_within_tolerance(setup_comp_2):
    """Test if humidity change doesn't turn off within tolerance."""
    humidifier = setup_comp_2
    _setup_switch(True)
    humidifier.humidity = 46
    main_loop.run_once()
    _setup_sensor(48)
    main_loop.run_once()
    assert len(calls) == 0


def test_humidity_change_humidifier_off_outside_tolerance(setup_comp_2):
    """Test if humidity change turn humidifier off outside wet tolerance."""
    humidifier = setup_comp_2
    _setup_switch(True)
    humidifier.humidity = 46
    _setup_sensor(50)
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert not call


def test_operation_mode_humidify(setup_comp_2):
    """Test change mode from OFF to HUMIDIFY.

    Switch turns on when humidity below setpoint and mode changes.
    """
    humidifier = setup_comp_2
    humidifier.state = False
    humidifier.humidity = 45
    _setup_sensor(40)
    _setup_switch(False)
    humidifier.state = True
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert call


def _setup_switch(is_on):
    """Set up the test switch."""
    humidifier_switch.state = is_on
    calls.clear()


def test_init_ignores_tolerance():
    """Test if tolerance is ignored on initialization."""
    _setup_switch(True)
    _setup_sensor(41)
    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=Switch(),
        target_humidity=40,
        dry_tolerance=4,
        wet_tolerance=2,
        away_humidity=30,
    )
    humidifier.state = True
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.state = False
    main_loop.run_once()


def test_running_when_operating_mode_is_off(setup_comp_2):
    """Test that the switch turns off when enabled is set False."""
    humidifier = setup_comp_2
    _setup_switch(True)
    _setup_sensor(55)
    humidifier.state = False
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert not call


def test_no_state_change_when_operation_mode_off(setup_comp_2):
    """Test that the switch doesn't turn on when enabled is False."""
    humidifier = setup_comp_2
    _setup_switch(False)
    _setup_sensor(60)
    humidifier.state = False
    _setup_sensor(35)
    main_loop.run_once()
    assert len(calls) == 0


@pytest.fixture
def setup_comp_4():
    """Initialize components."""
    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=Switch(),
        target_humidity=40,
        dry_tolerance=3,
        wet_tolerance=3,
    )
    humidifier.state = True
    yield humidifier
    humidifier.state = False
    main_loop.run_once()


def test_mode_change_humidifier_trigger_off_not_long_enough(setup_comp_4):
    """Test if mode change turns dry off despite minimum cycle."""
    humidifier = setup_comp_4
    _setup_switch(True)
    _setup_sensor(35)
    assert len(calls) == 0
    humidifier.state = False
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert not call


def test_mode_change_humidifier_trigger_on_not_long_enough(setup_comp_4):
    """Test if mode change turns dry on despite minimum cycle."""
    humidifier = setup_comp_4
    _setup_switch(False)
    _setup_sensor(45)
    humidifier.state = False
    _setup_sensor(35)
    main_loop.run_once()
    assert len(calls) == 0
    humidifier.state = True
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert call


def test_float_tolerance_values():
    """Test if humidifier does not turn on within floating point tolerance."""
    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=Switch(),
        target_humidity=40,
        wet_tolerance=0.2,
    )
    humidifier.state = True
    _setup_switch(True)
    main_loop.run_once()
    _setup_sensor(35)
    main_loop.run_once()
    _setup_sensor(40.1)
    main_loop.run_once()
    assert len(calls) == 0
    humidifier.state = False
    main_loop.run_once()


def test_float_tolerance_values_2():
    """Test if humidifier turns off when oudside of floating point tolerance values."""
    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=Switch(),
        target_humidity=40,
        wet_tolerance=0.2,
    )
    humidifier.state = True
    _setup_switch(True)
    _setup_sensor(40.3)
    assert len(calls) == 0
    main_loop.run_once()
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.state = False
    main_loop.run_once()


def test_custom_setup_params():
    """Test the setup with custom parameters."""
    _setup_sensor(45)
    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=Switch(),
        target_humidity=TARGET_HUMIDITY,
    )
    assert humidifier._target_humidity == TARGET_HUMIDITY
    humidifier.state = False
    main_loop.run_once()


def test_sensor_stale_duration(caplog):
    """Test turn off on sensor stale."""

    humidifier = Humidifier(
        switch=humidifier_switch,
        sensor=humidifier_sensor,
        available_sensor=Switch(),
        target_humidity=10,
        sensor_stale_duration=10 * 60,
    )
    humidifier.state = True

    _setup_sensor(23)
    main_loop.run_once()

    assert not humidifier_switch.state

    humidifier.humidity = 32
    main_loop.run_once()

    assert humidifier_switch.state

    # Wait 11 minutes
    mock_sleep(11 * 60)
    main_loop.run_once()

    # 11 minutes later, no news from the sensor : emergency cut off
    assert not humidifier_switch.state
    assert "emergency" in caplog.text

    # Updated value from sensor received
    _setup_sensor(24)
    main_loop.run_once()

    # A new value has arrived, the humidifier should go ON
    assert humidifier_switch.state

    # Manual turn off
    humidifier.state = False
    main_loop.run_once()
    assert not humidifier_switch.state

    # Wait another 11 minutes
    mock_sleep(11 * 60)
    main_loop.run_once()

    # Still off
    assert not humidifier_switch.state

    # Updated value from sensor received
    _setup_sensor(22)
    main_loop.run_once()

    # Not turning on by itself
    assert not humidifier.state
    assert not humidifier_switch.state
