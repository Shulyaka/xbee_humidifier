"""Main module of the humidifier."""

from gc import collect, mem_alloc, mem_free

import config
from commands import HumidifierCommands
from dutycycle import DutyCycle
from humidifier import GenericHygrostat
from lib import logging
from lib.core import Sensor, Switch
from lib.mainloop import main_loop
from machine import reset_cause
from micropython import kbd_intr

collect()

_LOGGER = logging.getLogger(__name__)


if config.debug:
    print("\nTOSR0X not detected, enabling emulation")

_LOGGER.debug("Reset cause {}".format(reset_cause()))


def _setup(debug):
    global _zone, _sensor, _commands, _available, _humidifier, _pump_block
    global _duty_cycle, _warning_subscribers, _warning_cb
    _zone = {x: Switch() for x in range(3)}
    _sensor = {x: Sensor() for x in range(3)}
    _available = {x: Switch() for x in range(3)}

    if debug:
        for x in range(3):
            _zone[x].subscribe(
                (lambda n: lambda v: print("ZONE{} = {}".format(n, v)))(x)
            )
            _sensor[x].subscribe(
                (lambda n: lambda v: print("SENSOR{} = {}".format(n, v)))(x)
            )
            _available[x].subscribe(
                (lambda n: lambda v: print("AVAILABLE{} = {}".format(n, v)))(x)
            )

        config.pump.subscribe(lambda v: print("PUMP = {}".format(v)))
        for x in range(4):
            config.valve_switch[x].subscribe(
                (lambda n: lambda v: print("VALVE{} = {}".format(n, v)))(x)
            )

        _prev_run_time = main_loop._run_time
        _prev_idle_time = main_loop._idle_time

        def _stats():
            """Print cpu stats."""
            nonlocal _prev_run_time, _prev_idle_time
            run_time = main_loop._run_time - _prev_run_time
            idle_time = main_loop._idle_time - _prev_idle_time
            _prev_run_time = main_loop._run_time
            _prev_idle_time = main_loop._idle_time

            alloc = mem_alloc()
            print(
                "CPU {:.2%}, MEM {:.2%}".format(
                    run_time / (run_time + idle_time)
                    if run_time + idle_time > 0
                    else 0,
                    alloc / (alloc + mem_free()),
                )
            )

        main_loop.schedule_task(_stats, period=1000)
        collect()

    _humidifier = {
        x: GenericHygrostat(
            switch=_zone[x],
            sensor=_sensor[x],
            available_sensor=_available[x],
            target_humidity=50,
            dry_tolerance=3,
            wet_tolerance=0,
            away_humidity=35,
            sensor_stale_duration=120 * 60,
        )
        for x in range(3)
    }
    collect()

    _pump_block = Switch()
    collect()

    if debug:
        for x in range(3):
            _humidifier[x].subscribe(
                (lambda n: lambda v: print("HUMIDIFIER{} = {}".format(n, v)))(x)
            )

        _pump_block.subscribe(lambda v: print("PUMP_BLOCK = {}".format(v)))
        collect()

    _duty_cycle = DutyCycle(
        config.pump, _humidifier, _zone, config.valve_switch, _pump_block
    )
    collect()

    _commands = HumidifierCommands(
        _humidifier,
        _sensor,
        _available,
        _zone,
        _pump_block,
    )
    collect()

    _warning_cb = main_loop.schedule_task(
        lambda: _LOGGER.warning("Not initialized"), period=30000
    )
    _warning_subscribers = {}

    def _cancel_warning(confirm):
        if not confirm:
            return

        global _available, _warning_cb, _warning_subscribers

        for x, unsub in _warning_subscribers.items():
            _available[x].unsubscribe(unsub)

        main_loop.remove_task(_warning_cb)

        _warning_subscribers.clear()
        _warning_subscribers = None
        _warning_cb = None
        collect()

    for x in range(3):
        _warning_subscribers[x] = _available[x].subscribe(_cancel_warning)

    main_loop.schedule_task(lambda: _LOGGER.debug("Main loop started"))

    if not debug:
        from machine import WDT

        _wdt = WDT(timeout=30000)
        main_loop.schedule_task(lambda: _wdt.feed(), period=1000)
        kbd_intr(-1)


_setup(config.debug)
_setup = None
collect()
