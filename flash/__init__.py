"""Main module of the humidifier."""

from gc import collect

from commands import HumidifierCommands
import config
from dutycycle import DutyCycle
from lib import logging
from lib.core import Sensor, Switch
from lib.humidifier import GenericHygrostat
from lib.mainloop import main_loop
from micropython import kbd_intr, mem_info

collect()

_LOGGER = logging.getLogger(__name__)


humidifier_zone = {x: Switch() for x in range(3)}
humidifier_sensor = {x: Sensor() for x in range(3)}
humidifier_available = {x: Switch() for x in range(3)}

if config.debug:
    zone_unsubscribe = {}
    sensor_unsubscribe = {}
    available_unsubscribe = {}
    for x in range(3):
        zone_unsubscribe[x] = humidifier_zone[x].subscribe(
            (lambda x: lambda v: print("zone" + str(x) + " = " + str(v)))(x)
        )
        sensor_unsubscribe[x] = humidifier_sensor[x].subscribe(
            (lambda x: lambda v: print("sensor" + str(x) + " = " + str(v)))(x)
        )
        available_unsubscribe[x] = humidifier_available[x].subscribe(
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
        switch_entity_id=humidifier_zone[x],
        sensor_entity_id=humidifier_sensor[x],
        available_sensor_id=humidifier_available[x],
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

duty_cycle = DutyCycle(
    config.pump, humidifier, humidifier_zone, config.valve_switch, pump_block
)

commands = HumidifierCommands(
    config.valve_switch,
    config.pump_temp,
    humidifier,
    humidifier_sensor,
    humidifier_available,
    humidifier_zone,
    config.pump,
    pump_block,
)

_cancel_warning_cb = main_loop.schedule_task(
    lambda: _LOGGER.warning("Not initialized"), period=30000
)
_unsubscribe_warning = {}


def _cancel_warning(confirm):
    if not confirm:
        return

    for unsub in _unsubscribe_warning.values():
        unsub()

    _cancel_warning_cb()


for x in range(3):
    _unsubscribe_warning[x] = humidifier_available[x].subscribe(_cancel_warning)

main_loop.schedule_task(lambda: _LOGGER.debug("Main loop started"))
