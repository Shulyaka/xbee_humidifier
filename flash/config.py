"""Humidifier config."""

from core import VirtualSensor, VirtualSwitch
from machine import Pin
from tosr import tosr_switch
from xbeepin import AnalogInput, AnalogOutput, DigitalInput, DigitalOutput

debug = True

if debug:
    pump = VirtualSwitch()
    valve_switch = {x: VirtualSwitch() for x in range(4)}
    pressure_in = VirtualSensor()
    pressure_out = VirtualSensor()
else:
    valve_switch = {x: tosr_switch[x + 1] for x in range(4)}
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
