"""Implementation of a slow PWM for humidifiers."""

import logging
from time import ticks_ms

from mainloop import main_loop
from micropython import const

_LOGGER = logging.getLogger(__name__)


class DutyCycle:
    """Slow PWM for humidifiers."""

    _pump = None
    _humidifier_switch = {}
    _valve_switch = {}
    _cancel_pump_timeout = None
    _cancel_close_valves = None
    _cancel_pressure_drop = None
    _pump_on_timeout_ms = const(6 * 60 * 1000)
    _pump_off_timeout_ms = const(3 * 60 * 1000)
    _pressure_drop_delay_ms = const(5 * 1000)
    _pressure_drop_time_ms = const(25 * 1000)
    _humidifier_unsubscribe = {}
    _switch_unsubscribe = {}

    def __init__(self, pump, humidifier, humidifier_switch, valve_switch, pump_block):
        """Init the class."""
        self._pump = pump
        self._humidifier = humidifier
        self._humidifier_switch = humidifier_switch
        self._valve_switch = valve_switch
        self._pump_block = pump_block

        self._pump.state = False
        self._pump_unsubscribe = self._pump.subscribe(lambda x: self._pump_changed(x))
        self._valve_unsubscribe = self._valve_switch[3].subscribe(
            lambda x: self._pressure_drop_valve_changed(x)
        )
        self._block_unsubscribe = self._pump_block.subscribe(
            lambda x: self._pump_block_changed(x)
        )
        for number, humidifier in self._humidifier.items():
            self._humidifier_unsubscribe[number] = humidifier.subscribe(
                lambda x: self._humidifier_changed(number, x)
            )
        for number, switch in self._humidifier_switch.items():
            self._switch_unsubscribe[number] = switch.subscribe(
                lambda x: self._switch_changed(number, x)
            )

        self.start_cycle()

    def __del__(self):
        """Cancel callbacks."""
        if self._cancel_pump_timeout:
            self._cancel_pump_timeout()
        if self._cancel_close_valves:
            self._cancel_close_valves()
        if self._cancel_pressure_drop:
            self._cancel_pressure_drop()
        self._pump_unsubscribe()
        self._valve_unsubscribe()
        self._block_unsubscribe()
        for humidifier_unsubscribe in self._humidifier_unsubscribe.values():
            humidifier_unsubscribe()
        for switch_unsubscribe in self._switch_unsubscribe.values():
            switch_unsubscribe()
        self._close_all_valves()

    def _humidifier_changed(self, number, value):
        """Handle humidifier on/off."""
        if value:
            self.start_cycle()
        else:
            self.stop_cycle()

    def _switch_changed(self, number, value):
        """Handle humidifier zone on/off."""
        if value:
            if self._cancel_pump_timeout is None:
                self.start_cycle()
        else:
            all_off = True
            for switch in self._humidifier_switch.items():
                if switch.state:
                    all_off = False
                    break
            if all_off:
                self.stop_cycle()

    def _pump_block_changed(self, value):
        """Handle block on/off."""
        if value:
            self.stop_cycle()
        else:
            self.start_cycle()

    def _pump_changed(self, value):
        """Handle pump on/off."""
        if self._cancel_pump_timeout is not None:
            self._cancel_pump_timeout()
        if self._cancel_pressure_drop is not None:
            self._cancel_pressure_drop()
        if self._cancel_close_valves is not None:
            self._cancel_close_valves()
            self._cancel_close_valves = None

        if value:
            self._cancel_pump_timeout = main_loop.schedule_task(
                lambda: self._pump_on_timeout(),
                next_time=ticks_ms() + self._pump_on_timeout_ms,
            )
            self._cancel_pressure_drop = None
        else:
            self._cancel_pump_timeout = main_loop.schedule_task(
                lambda: self._pump_off_timeout(),
                next_time=ticks_ms() + self._pump_off_timeout_ms,
            )
            self._cancel_pressure_drop = main_loop.schedule_task(
                lambda: self._start_pressure_drop(),
                next_time=ticks_ms() + self._pressure_drop_delay_ms,
            )

    def _pressure_drop_valve_changed(self, value):
        """Handle pressure drop valve on/off."""
        if self._cancel_pressure_drop is not None:
            self._cancel_pressure_drop()
            self._cancel_pressure_drop = None
        if self._cancel_close_valves is not None:
            self._cancel_close_valves()

        if value:
            self._cancel_close_valves = main_loop.schedule_task(
                lambda: self._close_all_valves(),
                next_time=ticks_ms() + self._pressure_drop_time_ms,
            )
        else:
            self._cancel_close_valves = None

    def _start_pressure_drop(self):
        """Initiate pressure drop."""
        self._valve_switch[3].state = True

    def _close_all_valves(self):
        """Complete pressure drop."""
        for switch in self._valve_switch.values():
            switch.state = False

    def _pump_on_timeout(self):
        """Handle pump staying on too long."""
        if self._cancel_pump_timeout is not None:
            self._cancel_pump_timeout()
            self._cancel_pump_timeout = None
        self.stop_cycle()

    def _pump_off_timeout(self):
        """Handle pump staying off too long."""
        if self._cancel_pump_timeout is not None:
            self._cancel_pump_timeout()
            self._cancel_pump_timeout = None
        self.start_cycle()

    def stop_cycle(self):
        """End duty cycle."""
        if not self._pump.state:
            _LOGGER.debug("The pump is already not running")
            return

        self._pump.state = False

    def start_cycle(self):
        """Enter duty cycle."""
        if self._pump.state:
            _LOGGER.debug("The pump is already running")
            return

        if (
            not self._humidifier_switch[0].state
            and not self._humidifier_switch[1].state
            and not self._humidifier_switch[2].state
        ):
            _LOGGER.debug("All switches are off, not starting the pump")
            return

        for x in range(3):
            self._valve_switch[x].state = self._humidifier_switch[x].state
        self._valve_switch[3].state = False

        self._pump.state = True
