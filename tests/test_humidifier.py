"""The tests for the generic_hygrostat."""
from time import sleep as mock_sleep
from unittest.mock import MagicMock

from lib.core import Sensor, Switch
from lib.humidifier import MODE_AWAY, MODE_NORMAL, GenericHygrostat
from lib.mainloop import main_loop
import pytest

ATTR_SAVED_HUMIDITY = "sav_hum"
MIN_HUMIDITY = 20
MAX_HUMIDITY = 65
TARGET_HUMIDITY = 42

humidifier_switch = Switch()
humidifier_sensor = Sensor()
humidifier_available = Switch()

calls = []
switch_unsubscribe = humidifier_switch.subscribe(lambda x: calls.append(x))


def test_heneric_hygrostat():
    """Test GenericHygrostat class."""
    humidifier = GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        min_humidity=15,
        max_humidity=100,
        target_humidity=50,
        dry_tolerance=3,
        wet_tolerance=0,
        initial_state=None,
        away_humidity=35,
        sensor_stale_duration=30 * 60,
    )

    assert isinstance(humidifier, Switch)

    callback = MagicMock()
    humidifier.subscribe(callback)

    assert not humidifier_available.state

    humidifier_sensor.state = 40
    assert humidifier_available.state
    assert not humidifier.state

    humidifier.state = True
    assert humidifier.state
    assert humidifier_switch.state
    callback.assert_called_once_with(True)

    callback.reset_mock()
    humidifier.state = False
    assert not humidifier.state
    assert not humidifier_switch.state
    callback.assert_called_once_with(False)


def test_humidifier_switch():
    """Test humidifier switching test switch."""
    humidifier = GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        initial_state=True,
    )

    assert not humidifier_switch.state

    _setup_sensor(23)

    humidifier.set_humidity(32)

    assert humidifier_switch.state
    humidifier.state = False


def _setup_sensor(humidity):
    """Set up the test sensor."""
    humidifier_sensor.state = humidity


@pytest.fixture
def setup_comp_0():
    """Initialize components."""
    _setup_sensor(45)
    humidifier_switch.state = False
    return GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        dry_tolerance=2,
        wet_tolerance=4,
        initial_state=True,
        away_humidity=35,
    )


@pytest.fixture
def setup_comp_2():
    """Initialize components."""
    _setup_sensor(45)

    return GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        dry_tolerance=2,
        wet_tolerance=4,
        initial_state=True,
        away_humidity=35,
    )


def test_unavailable_state():
    """Test the setting of defaults to unknown."""
    _setup_sensor("unavailable")
    humidifier = GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        dry_tolerance=2,
        wet_tolerance=4,
        away_humidity=35,
    )
    # The target sensor is unavailable, that should propagate to the humidifier entity:
    assert not humidifier_available.state

    # Sensor online
    _setup_sensor(30)
    assert humidifier_available.state
    assert not humidifier.state


def test_default_setup_params(setup_comp_2):
    """Test the setup with default parameters."""
    humidifier = setup_comp_2
    assert humidifier._min_humidity == 0
    assert humidifier._max_humidity == 100
    assert humidifier._target_humidity == 0
    humidifier.state = False


def test_set_target_humidity(setup_comp_2):
    """Test the setting of the target humidity."""
    humidifier = setup_comp_2
    humidifier.set_humidity(40)
    assert humidifier._target_humidity == 40
    with pytest.raises(TypeError):
        humidifier.set_humidity(None)
    with pytest.raises(ValueError):
        humidifier.set_humidity("str")
    assert humidifier._target_humidity == 40
    humidifier.state = False


def test_set_away_mode(setup_comp_2):
    """Test the setting away mode."""
    humidifier = setup_comp_2
    humidifier.set_humidity(44)
    humidifier.set_mode(MODE_AWAY)
    assert humidifier._target_humidity == 35
    humidifier.state = False


def test_set_away_mode_and_restore_prev_humidity(setup_comp_2):
    """Test the setting and removing away mode.

    Verify original humidity is restored.
    """
    humidifier = setup_comp_2
    humidifier.set_humidity(44)
    humidifier.set_mode(MODE_AWAY)
    assert humidifier._target_humidity == 35
    humidifier.set_mode(MODE_NORMAL)
    assert humidifier._target_humidity == 44
    humidifier.state = False


def test_set_away_mode_twice_and_restore_prev_humidity(setup_comp_2):
    """Test the setting away mode twice in a row.

    Verify original humidity is restored.
    """
    humidifier = setup_comp_2
    humidifier.set_humidity(44)
    humidifier.set_mode(MODE_AWAY)
    humidifier.set_mode(MODE_AWAY)
    assert humidifier._target_humidity == 35
    humidifier.set_mode(MODE_NORMAL)
    assert humidifier._target_humidity == 44
    humidifier.state = False


def test_set_target_humidity_humidifier_on(setup_comp_2):
    """Test if target humidity turn humidifier on."""
    humidifier = setup_comp_2
    _setup_switch(False)
    _setup_sensor(36)
    humidifier.set_humidity(45)
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.state = False


def test_set_target_humidity_humidifier_off(setup_comp_2):
    """Test if target humidity turn humidifier off."""
    humidifier = setup_comp_2
    _setup_switch(True)
    _setup_sensor(45)
    humidifier.set_humidity(36)
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.state = False


def test_humidity_change_humidifier_on_within_tolerance(setup_comp_2):
    """Test if humidity change doesn't turn on within tolerance."""
    humidifier = setup_comp_2
    _setup_switch(False)
    humidifier.set_humidity(44)
    _setup_sensor(43)
    assert len(calls) == 0
    humidifier.state = False


def test_humidity_change_humidifier_on_outside_tolerance(setup_comp_2):
    """Test if humidity change turn humidifier on outside dry tolerance."""
    humidifier = setup_comp_2
    _setup_switch(False)
    humidifier.set_humidity(44)
    _setup_sensor(42)
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.state = False


def test_humidity_change_humidifier_off_within_tolerance(setup_comp_2):
    """Test if humidity change doesn't turn off within tolerance."""
    humidifier = setup_comp_2
    _setup_switch(True)
    humidifier.set_humidity(46)
    _setup_sensor(48)
    assert len(calls) == 0
    humidifier.state = False


def test_humidity_change_humidifier_off_outside_tolerance(setup_comp_2):
    """Test if humidity change turn humidifier off outside wet tolerance."""
    humidifier = setup_comp_2
    _setup_switch(True)
    humidifier.set_humidity(46)
    _setup_sensor(50)
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.state = False


def test_operation_mode_humidify(setup_comp_2):
    """Test change mode from OFF to HUMIDIFY.

    Switch turns on when humidity below setpoint and mode changes.
    """
    humidifier = setup_comp_2
    humidifier.state = False
    humidifier.set_humidity(45)
    _setup_sensor(40)
    _setup_switch(False)
    humidifier.state = True
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.state = False


def _setup_switch(is_on):
    """Set up the test switch."""
    humidifier_switch.state = is_on
    calls.clear()


def test_init_ignores_tolerance():
    """Test if tolerance is ignored on initialization."""
    _setup_switch(True)
    _setup_sensor(41)
    humidifier = GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        dry_tolerance=4,
        wet_tolerance=2,
        initial_state=True,
        away_humidity=30,
    )
    assert 1 == len(calls)
    call = calls[0]
    assert not call
    humidifier.state = False


def test_running_when_operating_mode_is_off(setup_comp_2):
    """Test that the switch turns off when enabled is set False."""
    humidifier = setup_comp_2
    _setup_switch(True)
    _setup_sensor(55)
    humidifier.state = False
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
    assert len(calls) == 0


@pytest.fixture
def setup_comp_4():
    """Initialize components."""
    return GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        dry_tolerance=3,
        wet_tolerance=3,
        initial_state=True,
    )


def test_mode_change_humidifier_trigger_off_not_long_enough(setup_comp_4):
    """Test if mode change turns dry off despite minimum cycle."""
    humidifier = setup_comp_4
    _setup_switch(True)
    _setup_sensor(35)
    assert len(calls) == 0
    humidifier.state = False
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
    assert len(calls) == 0
    humidifier.state = True
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.state = False


def test_float_tolerance_values():
    """Test if humidifier does not turn on within floating point tolerance."""
    humidifier = GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        wet_tolerance=0.2,
        initial_state=True,
    )
    _setup_switch(True)
    _setup_sensor(35)
    _setup_sensor(40.1)
    assert len(calls) == 0
    humidifier.state = False


def test_float_tolerance_values_2():
    """Test if humidifier turns off when oudside of floating point tolerance values."""
    humidifier = GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        wet_tolerance=0.2,
        initial_state=True,
    )
    _setup_switch(True)
    _setup_sensor(40.3)
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.state = False


def test_custom_setup_params():
    """Test the setup with custom parameters."""
    _setup_sensor(45)
    humidifier = GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        min_humidity=MIN_HUMIDITY,
        max_humidity=MAX_HUMIDITY,
        target_humidity=TARGET_HUMIDITY,
    )
    assert humidifier._min_humidity == MIN_HUMIDITY
    assert humidifier._max_humidity == MAX_HUMIDITY
    assert humidifier._target_humidity == TARGET_HUMIDITY


def test_sensor_stale_duration(caplog):
    """Test turn off on sensor stale."""

    humidifier = GenericHygrostat(
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        initial_state=True,
        sensor_stale_duration=10 * 60,
    )

    _setup_sensor(23)

    assert not humidifier_switch.state

    humidifier.set_humidity(32)

    assert humidifier_switch.state

    # Wait 11 minutes
    mock_sleep(11 * 60)
    main_loop.run_once()

    # 11 minutes later, no news from the sensor : emergency cut off
    assert not humidifier_switch.state
    assert "emergency" in caplog.text

    # Updated value from sensor received
    _setup_sensor(24)

    # A new value has arrived, the humidifier should go ON
    assert humidifier_switch.state

    # Manual turn off
    humidifier.state = False
    assert not humidifier_switch.state

    # Wait another 11 minutes
    mock_sleep(11 * 60)
    main_loop.run_once()

    # Still off
    assert not humidifier_switch.state

    # Updated value from sensor received
    _setup_sensor(22)

    # Not turning on by itself
    assert not humidifier.state
    assert not humidifier_switch.state
