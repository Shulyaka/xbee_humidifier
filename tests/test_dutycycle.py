"""Test commands."""

import sys

sys.path.append("tests/modules")
sys.path.append("flash/lib")
sys.modules["time"] = __import__("mock_time")

from time import sleep as mock_sleep  # noqa: E402

from core import VirtualSensor, VirtualSwitch  # noqa: E402
from humidifier import GenericHygrostat  # noqa: E402
from mainloop import main_loop  # noqa: E402

from flash import dutycycle  # noqa: E402


def test_dutycycle():
    """Test DutyCycle class."""

    tosr_switch = {x: VirtualSwitch() for x in range(5)}

    humidifier_switch = {x: VirtualSwitch() for x in range(3)}
    humidifier_sensor = {x: VirtualSensor(40) for x in range(3)}
    humidifier_available = {x: VirtualSwitch() for x in range(3)}

    humidifier = {
        x: GenericHygrostat(
            name="humidifier" + str(x),
            switch_entity_id=humidifier_switch[x],
            sensor_entity_id=humidifier_sensor[x],
            available_sensor_id=humidifier_available[x],
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
        for x in range(3)
    }

    pump = VirtualSwitch()
    pump_block = VirtualSwitch()

    duty_cycle = dutycycle.DutyCycle(
        pump, humidifier, humidifier_switch, tosr_switch, pump_block
    )

    # Check initial state
    assert not pump.state
    assert not tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier[0].turn_on()
    humidifier[2].turn_on()

    # Make sure the cycle is not started until next loop
    assert not pump.state
    assert not tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    main_loop.run_once()

    # Check that the duty cycle is started
    assert pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(180)
    main_loop.run_once()

    # Check that the duty cycle is still running
    assert pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(180)
    main_loop.run_once()

    # Check that duty cycle has stopped, but the pressure drop valve isn't open yet
    assert not pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(5)
    main_loop.run_once()

    # Check that the pressure drop valve has opened
    assert not pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert tosr_switch[2].state
    assert tosr_switch[3].state

    mock_sleep(25)
    main_loop.run_once()

    # Check that the pressure drop has finished
    assert not pump.state
    assert not tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier_sensor[2].state = 55
    main_loop.run_once()

    # Humidifier switch 2 is closed, all valves remain closed
    assert not pump.state
    assert not tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(150)
    main_loop.run_once()

    # Check that duty cycle is started
    assert pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier[2].turn_off()

    # Check that duty cyucle is not stopped until next loop run
    assert pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    main_loop.run_once()

    # Check that duty cycle has stopped, but the pressure drop valve isn't open yet
    assert not pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier[2].turn_on()
    main_loop.run_once()

    # Check that duty cycle hasn't started because the humidifier switch is off
    assert not pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier[1].turn_on()
    main_loop.run_once()

    # Check that duty cycle has started
    assert pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(360)
    main_loop.run_once()

    # Check that duty cycle has stopped, but the pressure drop valve isn't open yet
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(5)
    humidifier[1].turn_off()
    main_loop.run_once()

    # Check that the pressure drop valve has opened
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert tosr_switch[3].state

    humidifier[1].turn_on()
    main_loop.run_once()

    # Check that duty cycle has started
    assert pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    duty_cycle.stop_cycle()

    # Check that duty cycle has stopped, but the pressure drop valve isn't open yet
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    duty_cycle.start_cycle()

    # Check that duty cycle has started
    assert pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state
