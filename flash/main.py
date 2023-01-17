"""Main module of the humidifier."""

import logging

from commands import register as commands_register
import config
from core import VirtualSensor, VirtualSwitch
from dutycycle import DutyCycle
from humidifier import GenericHygrostat
from mainloop import main_loop
from tosr import tosr_switch, tosr_temp

_LOGGER = logging.getLogger(__name__)


humidifier_switch = {x: VirtualSwitch() for x in range(3)}
humidifier_sensor = {x: VirtualSensor() for x in range(3)}
humidifier_available = {x: VirtualSwitch() for x in range(3)}


# for debug:
# import machine

switch_unsubscribe = {}
sensor_unsubscribe = {}
available_unsubscribe = {}
for x in range(3):
    switch_unsubscribe[x] = humidifier_switch[x].subscribe(
        (lambda x: lambda v: print("switch" + str(x) + " = " + str(v)))(x)
    )
    sensor_unsubscribe[x] = humidifier_sensor[x].subscribe(
        (lambda x: lambda v: print("sensor" + str(x) + " = " + str(v)))(x)
    )
    available_unsubscribe[x] = humidifier_available[x].subscribe(
        (lambda x: lambda v: print("available" + str(x) + " = " + str(v)))(x)
    )


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

pump_block = VirtualSwitch()

duty_cycle = DutyCycle(
    config.pump, humidifier, humidifier_switch, config.valve_switch, pump_block
)

commands_register(
    tosr_switch,
    tosr_temp,
    humidifier,
    humidifier_sensor,
    humidifier_available,
    humidifier_switch,
    config.pump,
    pump_block,
)

# definitely not for debug:
# from machine import WDT
# wdt = WDT(timeout=30000)
# main_loop.schedule_task(lambda: wdt.feed(), period=1000)

_LOGGER.debug("Main loop started")

main_loop.run()
