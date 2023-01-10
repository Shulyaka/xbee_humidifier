from tosr import tosr_switch, tosr_temp
from core import VirtualSwitch, VirtualSensor
from mainloop import main_loop
from humidifier import GenericHygrostat
from commands import register as commands_register
import logging

# _LOGGER = logging.getLogger(__name__)


humidifier_switch = {x: VirtualSwitch() for x in range(3)}
humidifier_sensor = {x: VirtualSensor() for x in range(3)}
humidifier_available = {x: VirtualSwitch() for x in range(3)}

pump = VirtualSwitch()

# for debug:
switch_unsubscribe = {}
sensor_unsubscribe = {}
available_unsubscribe = {}
for x in range(3):
    switch_unsubscribe[x] = humidifier_switch[x].subscribe(
        lambda v: print("switch" + str(x) + " = " + str(v))
    )
    sensor_unsubscribe[x] = humidifier_sensor[x].subscribe(
        lambda v: print("sensor" + str(x) + " = " + str(v))
    )
    available_unsubscribe[x] = humidifier_available[x].subscribe(
        lambda v: print("available" + str(x) + " = " + str(v))
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

commands_register(
    tosr_switch,
    tosr_temp,
    humidifier,
    humidifier_sensor,
    humidifier_available,
    humidifier_switch,
)

import machine

main_loop.run()
