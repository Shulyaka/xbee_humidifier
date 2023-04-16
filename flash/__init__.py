"""Main module of the humidifier."""

from gc import collect

from commands import HumidifierCommands
import config
from dutycycle import DutyCycle
from humidifier import GenericHygrostat
from lib import logging
from lib.core import Sensor, Switch
from lib.mainloop import main_loop
from machine import reset_cause
from micropython import kbd_intr, mem_info

collect()

_LOGGER = logging.getLogger(__name__)


if config.debug:
    print("Reset cause %s" % reset_cause())

_LOGGER.debug("Reset cause %s", reset_cause())

zone = {x: Switch() for x in range(3)}
sensor = {x: Sensor() for x in range(3)}
available = {x: Switch() for x in range(3)}

if config.debug:
    zone_unsubscribe = {}
    sensor_unsubscribe = {}
    available_unsubscribe = {}
    for x in range(3):
        zone_unsubscribe[x] = zone[x].subscribe(
            (lambda x: lambda v: print("zone" + str(x) + " = " + str(v)))(x)
        )
        sensor_unsubscribe[x] = sensor[x].subscribe(
            (lambda x: lambda v: print("sensor" + str(x) + " = " + str(v)))(x)
        )
        available_unsubscribe[x] = available[x].subscribe(
            (lambda x: lambda v: print("available" + str(x) + " = " + str(v)))(x)
        )

    pump_unsubscribe = config.pump.subscribe(lambda v: print("pump = " + str(v)))
    valve_unsubscribe = {}
    for x in range(4):
        valve_unsubscribe[x] = config.valve_switch[x].subscribe(
            (lambda x: lambda v: print("valve" + str(x) + " = " + str(v)))(x)
        )

    main_loop.schedule_task(mem_info, period=30000)

    prev_run_time = main_loop._run_time
    prev_idle_time = main_loop._idle_time

    def cpu_stats():
        """Print cpu stats."""
        global prev_run_time, prev_idle_time
        run_time = main_loop._run_time - prev_run_time
        idle_time = main_loop._idle_time - prev_idle_time
        prev_run_time = main_loop._run_time
        prev_idle_time = main_loop._idle_time
        print("CPU " + str(run_time * 100 / (run_time + idle_time)) + "%")

    cpu_stats_cancel = main_loop.schedule_task(cpu_stats, period=1000)
else:
    from machine import WDT

    wdt = WDT(timeout=30000)
    main_loop.schedule_task(lambda: wdt.feed(), period=1000)
    kbd_intr(-1)

    # main_loop.schedule_task(mem_info, period=30000)


humidifier = {
    x: GenericHygrostat(
        switch_entity_id=zone[x],
        sensor_entity_id=sensor[x],
        available_sensor_id=available[x],
        min_humidity=15,
        max_humidity=100,
        target_humidity=50,
        dry_tolerance=3,
        wet_tolerance=0,
        initial_state=None,
        away_humidity=35,
        sensor_stale_duration=30 * 60,
    )
    for x in range(3)
}

pump_block = Switch()

if config.debug:
    humidifier_unsubscribe = {}
    for x in range(3):
        humidifier_unsubscribe[x] = humidifier[x].subscribe(
            (lambda x: lambda v: print("humidifier" + str(x) + " = " + str(v)))(x)
        )

    pump_block_unsubscribe = pump_block.subscribe(
        lambda v: print("pump_block = " + str(v))
    )

duty_cycle = DutyCycle(config.pump, humidifier, zone, config.valve_switch, pump_block)

commands = HumidifierCommands(
    humidifier,
    sensor,
    available,
    zone,
    pump_block,
)

_cancel_warning_cb = main_loop.schedule_task(
    lambda: _LOGGER.warning("Not initialized"), period=30000
)
_unsubscribe_warning = {}


def _cancel_warning(confirm):
    if not confirm:
        return

    global _cancel_warning_cb, _unsubscribe_warning

    for unsub in _unsubscribe_warning.values():
        unsub()

    _cancel_warning_cb()

    _unsubscribe_warning.clear()
    _unsubscribe_warning = None
    _cancel_warning_cb = None


for x in range(3):
    _unsubscribe_warning[x] = available[x].subscribe(_cancel_warning)

main_loop.schedule_task(lambda: _LOGGER.debug("Main loop started"))
