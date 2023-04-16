"""Humidifier config."""

from micropython import const

debug = const(True)

if debug:
    from lib.core import Sensor, Switch

    pump = Switch()
    pump_temp = Sensor(37)
    valve_switch = {x: Switch() for x in range(4)}
    pressure_in = Sensor(7)
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
