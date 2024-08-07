"""Humidifier config."""

from gc import collect

from micropython import const
from tosr0x import tosr0x_version

pump_on_timeout = const(10 * 60)
pressure_drop_delay = const(8)
pressure_drop_time = const(52)
idle_time = const(2 * 60)

debug = False

if tosr0x_version() is None:
    from lib.core import Sensor, Switch

    collect()
    debug = True
    pump = Switch()
    pump_temp = Sensor(37)
    valve_switch = [Switch() for x in range(4)]
    pressure_in = Sensor(1234)
    pressure_out = Sensor(59)  # Ignored for now
    water_temperature = Sensor(14)  # Ignored for now
    aux_din = Switch(False)  # Ignored for now
    aux_led = Switch(False)
    pump_speed = Sensor(255)
    fan = Switch(False)
else:
    from lib.xbeepin import AnalogInput, AnalogOutput, DigitalInput, DigitalOutput
    from machine import Pin
    from tosr import tosr_switch as valve_switch, tosr_temp as pump_temp  # noqa: F401

    collect()
    Pin("D0", mode=Pin.ALT, alt=Pin.AF0_COMMISSION)
    pressure_in = AnalogInput("D1")
    pressure_out = AnalogInput("D2")
    water_temperature = AnalogInput("D3")
    aux_din = DigitalInput("D4")
    Pin("D5", mode=Pin.ALT, alt=Pin.AF5_ASSOC_IND)
    # D6 = NC, D7 = NC
    pump = DigitalOutput("D8")
    aux_led = DigitalOutput("D9")
    Pin("D10", mode=Pin.ALT, alt=Pin.AF10_RSSI)
    pump_speed = AnalogOutput("D11")
    fan = DigitalOutput("D12")

collect()
