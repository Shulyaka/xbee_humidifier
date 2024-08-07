"""Test duty cycle."""

from time import sleep as mock_sleep

import dutycycle
from humidifier import Humidifier
from lib.core import Sensor, Switch
from lib.mainloop import main_loop


def test_dutycycle():
    """Test DutyCycle class."""

    tosr_switch = [Switch() for x in range(5)]

    humidifier_switch = [Switch() for x in range(3)]
    humidifier_sensor = [Sensor(40) for x in range(3)]
    humidifier_available = [Switch() for x in range(3)]

    humidifier = [
        Humidifier(
            switch=humidifier_switch[x],
            sensor=humidifier_sensor[x],
            available_sensor=humidifier_available[x],
            target_humidity=50,
            dry_tolerance=3,
            wet_tolerance=0,
            away_humidity=35,
            sensor_stale_duration=30 * 60,
        )
        for x in range(3)
    ]

    pump = Switch()
    pump_block = Switch()

    pump_on_timeout = 7 * 60
    pressure_drop_delay = 5
    pressure_drop_time = 55
    idle_time = 2 * 60

    duty_cycle = dutycycle.DutyCycle(
        pump,
        humidifier,
        humidifier_switch,
        tosr_switch,
        pump_block,
        pump_on_timeout,
        pressure_drop_delay,
        pressure_drop_time,
        idle_time,
    )

    assert (
        duty_cycle._pump_off_timeout_ms
        > duty_cycle._pressure_drop_delay_ms + duty_cycle._pressure_drop_time_ms
    )

    assert pump_on_timeout == duty_cycle._pump_on_timeout_ms / 1000
    assert (
        idle_time + pressure_drop_delay + pressure_drop_time
        == duty_cycle._pump_off_timeout_ms / 1000
    )
    assert pressure_drop_delay == duty_cycle._pressure_drop_delay_ms / 1000
    assert pressure_drop_time == duty_cycle._pressure_drop_time_ms / 1000

    # Check initial state
    assert not pump.state
    assert not tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier[0].state = True
    humidifier[2].state = True

    # Make sure the cycle is not started until next loop
    assert not pump.state
    assert not tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    main_loop.run_once()
    main_loop.run_once()

    # Check that the duty cycle is started
    assert pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(pump_on_timeout / 2)
    main_loop.run_once()

    # Check that the duty cycle is still running
    assert pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(pump_on_timeout / 2)
    main_loop.run_once()

    # Check that duty cycle has stopped, but the pressure drop valve isn't open yet
    assert not pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(pressure_drop_delay)
    main_loop.run_once()

    # Check that the pressure drop valve has opened
    assert not pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert tosr_switch[2].state
    assert tosr_switch[3].state

    mock_sleep(pressure_drop_time)
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

    mock_sleep(idle_time)
    main_loop.run_once()

    # Check that duty cycle is started
    assert pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier[2].state = False
    main_loop.run_once()

    # Check that duty cycle is not stopped until next loop run
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

    humidifier[2].state = True
    main_loop.run_once()

    # Check that duty cycle hasn't started because the humidifier switch is off
    assert not pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier[1].state = True
    main_loop.run_once()
    main_loop.run_once()

    # Check that duty cycle has started
    assert pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(pump_on_timeout)
    main_loop.run_once()

    # Check that duty cycle has stopped, but the pressure drop valve isn't open yet
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    mock_sleep(pressure_drop_delay)
    humidifier[1].state = False
    main_loop.run_once()

    # Check that the pressure drop valve has opened
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert tosr_switch[3].state

    humidifier[1].state = True
    main_loop.run_once()
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

    duty_cycle.start_cycle()

    # Check that duty cycle start when it is already running does not stop it
    assert pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    pump_block.state = True
    main_loop.run_once()

    # Check that the pump block stops the duty cycle
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    duty_cycle.start_cycle()

    # Check that manual duty cycle start is blocked
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    pump.state = True
    main_loop.run_once()

    # Check that the pump did not start due to the pump block
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    pump_block.state = False
    pump_block.state = True
    main_loop.run_once()

    # Check that pump unblock and block in quick succession keeps cycle stopped
    assert not pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    pump_block.state = False
    main_loop.run_once()

    # Check that pump unblock starts the cycle back
    assert pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    pump_block.state = True
    pump_block.state = False
    main_loop.run_once()

    # Check that pump block and unblock in quick succession keeps cycle running
    assert pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier_sensor[1].state = 55
    main_loop.run_once()

    # Check that single zone off does not stop the cycle if there are open zones
    assert pump.state
    assert tosr_switch[0].state
    assert tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    duty_cycle.stop_cycle()
    main_loop.run_once()

    mock_sleep(pressure_drop_delay)
    main_loop.run_once()

    mock_sleep(pressure_drop_time)
    main_loop.run_once()

    # Check that pressure drop valve is closed
    assert not pump.state
    assert not tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    humidifier[1].state = False
    main_loop.run_once()

    pump_block.state = True
    humidifier[1].state = True
    main_loop.run_once()

    # Check that the pump start has been blocked
    assert not pump.state
    assert not tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state

    pump_block.state = False
    humidifier_sensor[0].state = 55
    main_loop.run_once()
    main_loop.run_once()

    # Check that the cycle has started, then stopped
    assert not pump.state
    assert tosr_switch[0].state
    assert not tosr_switch[1].state
    assert not tosr_switch[2].state
    assert not tosr_switch[3].state
