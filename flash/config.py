"""Humidifier config."""

debug = True

if debug:
    from lib.core import VirtualSensor, VirtualSwitch

    pump = VirtualSwitch()
    pump_temp = VirtualSensor(37)
    valve_switch = {x: VirtualSwitch() for x in range(4)}
    pressure_in = VirtualSensor(7)
    pressure_out = VirtualSensor(59)
else:
    from lib.tosr import tosr_switch, tosr_temp
    from lib.xbeepin import AnalogInput, AnalogOutput, DigitalInput, DigitalOutput
    from machine import Pin

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
    pump_temp = tosr_temp
