"""The tests for the generic_hygrostat."""
import sys

import pytest

sys.path.append("tests/modules")
sys.path.append("flash/lib")
sys.modules["time"] = __import__("mock_time")

from time import sleep as mock_sleep  # noqa: E402

from core import VirtualSensor, VirtualSwitch  # noqa: E402
from mainloop import main_loop  # noqa: E402

from flash.lib.humidifier import MODE_AWAY, MODE_NORMAL, GenericHygrostat  # noqa: E402

ATTR_SAVED_HUMIDITY = "saved_humidity"
MIN_HUMIDITY = 20
MAX_HUMIDITY = 65
TARGET_HUMIDITY = 42

humidifier_switch = VirtualSwitch()
humidifier_sensor = VirtualSensor()
humidifier_available = VirtualSwitch()

calls = []
switch_unsubscribe = humidifier_switch.subscribe(lambda x: calls.append(x))


def test_heneric_hygrostat():
    """Test GenericHygrostat class."""
    humidifier = GenericHygrostat(
        name="test_humidifier",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        min_humidity=15,
        max_humidity=100,
        target_humidity=50,
        device_class="humidifier",
        dry_tolerance=3,
        wet_tolerance=0,
        initial_state=None,
        away_humidity=35,
        away_fixed=False,
        sensor_stale_duration=30 * 60,
    )

    assert not humidifier.available

    humidifier_sensor.state = 40
    assert humidifier_available.state
    assert not humidifier.is_on

    humidifier.turn_on()
    assert humidifier_switch.state

    humidifier.turn_off()
    assert not humidifier_switch.state


def test_humidifier_switch():
    """Test humidifier switching test switch."""
    humidifier = GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        initial_state=True,
    )

    assert not humidifier_switch.state

    _setup_sensor(23)

    humidifier.set_humidity(32)

    assert humidifier_switch.state
    humidifier.turn_off()


def _setup_sensor(humidity):
    """Set up the test sensor."""
    humidifier_sensor.state = humidity


@pytest.fixture
def setup_comp_0():
    """Initialize components."""
    _setup_sensor(45)
    humidifier_switch.state = False
    return GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        device_class="dehumidifier",
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
        name="test",
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
    _setup_sensor(None)
    humidifier = GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        dry_tolerance=2,
        wet_tolerance=4,
        away_humidity=35,
    )
    # The target sensor is unavailable, that should propagate to the humidifier entity:
    assert not humidifier.available

    # Sensor online
    _setup_sensor(30)
    assert humidifier.available
    assert not humidifier.state


def test_default_setup_params(setup_comp_2):
    """Test the setup with default parameters."""
    humidifier = setup_comp_2
    assert humidifier.min_humidity == 0
    assert humidifier.max_humidity == 100
    assert humidifier.target_humidity == 0
    humidifier.turn_off()


def test_default_setup_params_dehumidifier(setup_comp_0):
    """Test the setup with default parameters for dehumidifier."""
    humidifier = setup_comp_0
    assert humidifier.min_humidity == 0
    assert humidifier.max_humidity == 100
    assert humidifier.target_humidity == 100
    humidifier.turn_off()


def test_get_modes(setup_comp_2):
    """Test that the attributes returns the correct modes."""
    humidifier = setup_comp_2
    modes = humidifier.available_modes
    assert modes == [MODE_NORMAL, MODE_AWAY]
    humidifier.turn_off()


def test_set_target_humidity(setup_comp_2):
    """Test the setting of the target humidity."""
    humidifier = setup_comp_2
    humidifier.set_humidity(40)
    assert humidifier.target_humidity == 40
    with pytest.raises(TypeError):
        humidifier.set_humidity(None)
    with pytest.raises(ValueError):
        humidifier.set_humidity("str")
    assert humidifier.target_humidity == 40
    humidifier.turn_off()


def test_set_away_mode(setup_comp_2):
    """Test the setting away mode."""
    humidifier = setup_comp_2
    humidifier.set_humidity(44)
    humidifier.set_mode(MODE_AWAY)
    assert humidifier.target_humidity == 35
    humidifier.turn_off()


def test_set_away_mode_and_restore_prev_humidity(setup_comp_2):
    """Test the setting and removing away mode.

    Verify original humidity is restored.
    """
    humidifier = setup_comp_2
    humidifier.set_humidity(44)
    humidifier.set_mode(MODE_AWAY)
    assert humidifier.target_humidity == 35
    humidifier.set_mode(MODE_NORMAL)
    assert humidifier.target_humidity == 44
    humidifier.turn_off()


def test_set_away_mode_twice_and_restore_prev_humidity(setup_comp_2):
    """Test the setting away mode twice in a row.

    Verify original humidity is restored.
    """
    humidifier = setup_comp_2
    humidifier.set_humidity(44)
    humidifier.set_mode(MODE_AWAY)
    humidifier.set_mode(MODE_AWAY)
    assert humidifier.target_humidity == 35
    humidifier.set_mode(MODE_NORMAL)
    assert humidifier.target_humidity == 44
    humidifier.turn_off()


def test_set_target_humidity_humidifier_on(setup_comp_2):
    """Test if target humidity turn humidifier on."""
    humidifier = setup_comp_2
    _setup_switch(False)
    _setup_sensor(36)
    humidifier.set_humidity(45)
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.turn_off()


def test_set_target_humidity_humidifier_off(setup_comp_2):
    """Test if target humidity turn humidifier off."""
    humidifier = setup_comp_2
    _setup_switch(True)
    _setup_sensor(45)
    humidifier.set_humidity(36)
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.turn_off()


def test_humidity_change_humidifier_on_within_tolerance(setup_comp_2):
    """Test if humidity change doesn't turn on within tolerance."""
    humidifier = setup_comp_2
    _setup_switch(False)
    humidifier.set_humidity(44)
    _setup_sensor(43)
    assert len(calls) == 0
    humidifier.turn_off()


def test_humidity_change_humidifier_on_outside_tolerance(setup_comp_2):
    """Test if humidity change turn humidifier on outside dry tolerance."""
    humidifier = setup_comp_2
    _setup_switch(False)
    humidifier.set_humidity(44)
    _setup_sensor(42)
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.turn_off()


def test_humidity_change_humidifier_off_within_tolerance(setup_comp_2):
    """Test if humidity change doesn't turn off within tolerance."""
    humidifier = setup_comp_2
    _setup_switch(True)
    humidifier.set_humidity(46)
    _setup_sensor(48)
    assert len(calls) == 0
    humidifier.turn_off()


def test_humidity_change_humidifier_off_outside_tolerance(setup_comp_2):
    """Test if humidity change turn humidifier off outside wet tolerance."""
    humidifier = setup_comp_2
    _setup_switch(True)
    humidifier.set_humidity(46)
    _setup_sensor(50)
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.turn_off()


def test_operation_mode_humidify(setup_comp_2):
    """Test change mode from OFF to HUMIDIFY.

    Switch turns on when humidity below setpoint and mode changes.
    """
    humidifier = setup_comp_2
    humidifier.turn_off()
    humidifier.set_humidity(45)
    _setup_sensor(40)
    _setup_switch(False)
    humidifier.turn_on()
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.turn_off()


def _setup_switch(is_on):
    """Set up the test switch."""
    humidifier_switch.state = is_on
    calls.clear()


@pytest.fixture
def setup_comp_3():
    """Initialize components."""
    return GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        device_class="dehumidifier",
        dry_tolerance=2,
        wet_tolerance=4,
        initial_state=True,
        away_humidity=30,
    )


def test_set_target_humidity_dry_off(setup_comp_3):
    """Test if target humidity turn dry off."""
    humidifier = setup_comp_3
    _setup_switch(True)
    _setup_sensor(50)
    humidifier.set_humidity(55)
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.turn_off()


def test_turn_away_mode_on_drying(setup_comp_3):
    """Test the setting away mode when drying."""
    humidifier = setup_comp_3
    _setup_switch(True)
    _setup_sensor(50)
    humidifier.set_humidity(34)
    humidifier.set_mode(MODE_AWAY)
    assert humidifier.target_humidity == 30
    humidifier.turn_off()


def test_operation_mode_dry(setup_comp_3):
    """Test change mode from OFF to DRY.

    Switch turns on when humidity below setpoint and state changes.
    """
    humidifier = setup_comp_3
    _setup_switch(False)
    _setup_sensor(30)
    assert len(calls) == 0
    humidifier.turn_off()
    _setup_sensor(45)
    assert len(calls) == 0
    humidifier.turn_on()
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.turn_off()


def test_set_target_humidity_dry_on(setup_comp_3):
    """Test if target humidity turn dry on."""
    humidifier = setup_comp_3
    _setup_switch(False)
    _setup_sensor(45)
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.turn_off()


def test_init_ignores_tolerance():
    """Test if tolerance is ignored on initialization."""
    _setup_switch(True)
    _setup_sensor(39)
    humidifier = GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        device_class="dehumidifier",
        dry_tolerance=2,
        wet_tolerance=4,
        initial_state=True,
        away_humidity=30,
    )
    assert 1 == len(calls)
    call = calls[0]
    assert not call
    humidifier.turn_off()


def test_humidity_change_dry_off_within_tolerance(setup_comp_3):
    """Test if humidity change doesn't turn dry off within tolerance."""
    humidifier = setup_comp_3
    _setup_switch(True)
    _setup_sensor(45)
    _setup_sensor(39)
    assert len(calls) == 0
    humidifier.turn_off()


def test_set_humidity_change_dry_off_outside_tolerance(setup_comp_3):
    """Test if humidity change turn dry off."""
    humidifier = setup_comp_3
    _setup_switch(True)
    _setup_sensor(36)
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.turn_off()


def test_humidity_change_dry_on_within_tolerance(setup_comp_3):
    """Test if humidity change doesn't turn dry on within tolerance."""
    humidifier = setup_comp_3
    _setup_switch(False)
    _setup_sensor(37)
    _setup_sensor(41)
    assert len(calls) == 0
    humidifier.turn_off()


def test_humidity_change_dry_on_outside_tolerance(setup_comp_3):
    """Test if humidity change turn dry on."""
    humidifier = setup_comp_3
    _setup_switch(False)
    _setup_sensor(45)
    assert len(calls) == 1
    call = calls[0]
    assert call
    humidifier.turn_off()


def test_running_when_operating_mode_is_off_2(setup_comp_3):
    """Test that the switch turns off when enabled is set False."""
    humidifier = setup_comp_3
    _setup_switch(True)
    _setup_sensor(45)
    humidifier.turn_off()
    assert len(calls) == 1
    call = calls[0]
    assert not call


def test_no_state_change_when_operation_mode_off_2(setup_comp_3):
    """Test that the switch doesn't turn on when enabled is False."""
    humidifier = setup_comp_3
    _setup_switch(False)
    _setup_sensor(30)
    humidifier.turn_off()
    _setup_sensor(45)
    assert len(calls) == 0


@pytest.fixture
def setup_comp_4():
    """Initialize components."""
    return GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        device_class="dehumidifier",
        dry_tolerance=3,
        wet_tolerance=3,
        initial_state=True,
    )


def test_mode_change_dry_trigger_off_not_long_enough(setup_comp_4):
    """Test if mode change turns dry off despite minimum cycle."""
    humidifier = setup_comp_4
    _setup_switch(True)
    _setup_sensor(45)
    assert len(calls) == 0
    humidifier.turn_off()
    assert len(calls) == 1
    call = calls[0]
    assert not call


def test_mode_change_dry_trigger_on_not_long_enough(setup_comp_4):
    """Test if mode change turns dry on despite minimum cycle."""
    humidifier = setup_comp_4
    _setup_switch(False)
    _setup_sensor(35)
    humidifier.turn_off()
    _setup_sensor(45)
    assert len(calls) == 0
    humidifier.turn_on()
    assert len(calls) == 1
    call = calls[0]
    assert call


def test_float_tolerance_values():
    """Test if dehumidifier does not turn on within floating point tolerance."""
    humidifier = GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        device_class="dehumidifier",
        dry_tolerance=0.2,
        initial_state=True,
    )
    _setup_switch(True)
    _setup_sensor(45)
    _setup_sensor(39.9)
    assert len(calls) == 0
    humidifier.turn_off()


def test_float_tolerance_values_2():
    """Test if dehumidifier turns off when oudside of floating point tolerance values."""
    humidifier = GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        device_class="dehumidifier",
        dry_tolerance=0.2,
        initial_state=True,
    )
    _setup_switch(True)
    _setup_sensor(39.7)
    assert len(calls) == 1
    call = calls[0]
    assert not call
    humidifier.turn_off()


def test_custom_setup_params():
    """Test the setup with custom parameters."""
    _setup_sensor(45)
    humidifier = GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        min_humidity=MIN_HUMIDITY,
        max_humidity=MAX_HUMIDITY,
        target_humidity=TARGET_HUMIDITY,
    )
    assert humidifier.min_humidity == MIN_HUMIDITY
    assert humidifier.max_humidity == MAX_HUMIDITY
    assert humidifier.target_humidity == TARGET_HUMIDITY


def test_away_fixed_humidity_mode():
    """Ensure retain of target humidity for normal mode."""
    _setup_sensor(45)
    test_hygrostat = GenericHygrostat(
        name="test",
        switch_entity_id=humidifier_switch,
        sensor_entity_id=humidifier_sensor,
        available_sensor_id=humidifier_available,
        target_humidity=40,
        away_humidity=32,
        away_fixed=True,
    )

    assert test_hygrostat.target_humidity == 40
    assert test_hygrostat.mode == MODE_NORMAL
    assert not test_hygrostat.state

    # Switch to Away mode
    test_hygrostat.set_mode(MODE_AWAY)

    # Target humidity changed to away_humidity
    assert test_hygrostat.mode == MODE_AWAY
    assert test_hygrostat.target_humidity == 32
    assert test_hygrostat.extra_state_attributes[ATTR_SAVED_HUMIDITY] == 40
    assert not test_hygrostat.state

    # Change target humidity
    test_hygrostat.set_humidity(42)

    # Current target humidity not changed
    assert test_hygrostat.target_humidity == 32
    assert test_hygrostat.extra_state_attributes[ATTR_SAVED_HUMIDITY] == 42
    assert test_hygrostat.mode == MODE_AWAY
    assert not test_hygrostat.state

    # Return to Normal mode
    test_hygrostat.set_mode(MODE_NORMAL)

    # Target humidity changed to away_humidity
    assert test_hygrostat.target_humidity == 42
    assert test_hygrostat.extra_state_attributes[ATTR_SAVED_HUMIDITY] == 32
    assert test_hygrostat.mode == MODE_NORMAL
    assert not test_hygrostat.state


def test_sensor_stale_duration(caplog):
    """Test turn off on sensor stale."""

    humidifier = GenericHygrostat(
        name="test",
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
    humidifier.turn_off()
    assert not humidifier_switch.state

    # Wait another 11 minutes
    mock_sleep(11 * 60)
    main_loop.run_once()

    # Still off
    assert not humidifier_switch.state

    # Updated value from sensor received
    _setup_sensor(22)

    # Not turning on by itself
    assert not humidifier_switch.state
