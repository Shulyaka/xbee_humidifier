"""Main module of the humidifier."""

from gc import collect, mem_alloc, mem_free

import config
from commands import HumidifierCommands
from dutycycle import DutyCycle
from humidifier import Humidifier
from lib import logging
from lib.core import Sensor, Switch
from lib.mainloop import main_loop
from micropython import kbd_intr

collect()

_LOGGER = logging.getLogger(__name__)


def _setup(debug):
    global _zone, _sensor, _commands, _available, _humidifier, _pump_block, _duty_cycle
    _zone = {x: Switch() for x in range(3)}
    _sensor = {x: Sensor() for x in range(3)}
    _available = {x: Switch() for x in range(3)}

    if debug:
        print("\nTOSR0X not detected, enabling emulation")

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

        def _stats():
            """Print mem stats."""
            alloc = mem_alloc()
            print("MEM {:.2%}".format(alloc / (alloc + mem_free())))

        main_loop.schedule_task(_stats, period=1000)
        collect()

    _humidifier = {
        x: Humidifier(
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
        config.pump,
        _humidifier,
        _zone,
        config.valve_switch,
        _pump_block,
        config.pump_on_timeout,
        config.pressure_drop_delay,
        config.pressure_drop_time,
        config.idle_time,
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

    main_loop.schedule_task(lambda: _LOGGER.debug("Main loop started"))

    if not debug:
        from machine import WDT

        _wdt = WDT(timeout=30000)
        main_loop.schedule_task(lambda: _wdt.feed(), period=1000)
        kbd_intr(-1)


_setup(config.debug)
_setup = None
collect()
