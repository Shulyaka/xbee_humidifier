"""Implementation of a slow PWM for humidifiers."""

from time import ticks_add, ticks_ms

from lib import logging
from lib.mainloop import main_loop
from micropython import const

_LOGGER = logging.getLogger(__name__)


class DutyCycle:
    """Slow PWM for humidifiers."""

    _pump_on_timeout_ms = const(6 * 60 * 1000)
    _pump_off_timeout_ms = const(3 * 60 * 1000)
    _pressure_drop_delay_ms = const(5 * 1000)
    _pressure_drop_time_ms = const(55 * 1000)

    def __init__(self, pump, humidifiers, zone, valve_switch, pump_block):
        """Init the class."""
        self._pump = pump
        self._humidifier = humidifiers
        self._zone = zone
        self._valve_switch = valve_switch
        self._pump_block = pump_block

        self._pump.state = False

        self._pump_timeout = None
        self._close_valves = None
        self._pressure_drop = None
        self._loop_schedule = None

        self._pump_subscriber = self._pump.subscribe(lambda x: self._pump_changed(x))
        self._valve_subscriber = self._valve_switch[3].subscribe(
            lambda x: self._pressure_drop_valve_changed(x)
        )
        self._block_subscriber = self._pump_block.subscribe(
            lambda x: self._pump_block_changed(x)
        )

        self._humidifier_subscriber = {}
        for number, humidifier in self._humidifier.items():
            self._humidifier_subscriber[number] = humidifier.subscribe(
                (
                    lambda n: lambda x: main_loop.schedule_task(
                        lambda: self._humidifier_changed(n, x)
                    )
                )(number)
            )

        self._zone_subscriber = {}
        for number, zone in self._zone.items():
            self._zone_subscriber[number] = zone.subscribe(
                (lambda n: lambda x: self._zone_changed(n, x))(number)
            )

        self.start_cycle()

    def __del__(self):
        """Cancel callbacks."""
        self.stop_cycle()
        main_loop.remove_task(self._loop_schedule)
        main_loop.remove_task(self._pump_timeout)
        main_loop.remove_task(self._close_valves)
        main_loop.remove_task(self._pressure_drop)
        self._pump.unsubscribe(self._pump_subscriber)
        self._valve_switch[3].unsubscribe(self._valve_subscriber)
        self._pump_block.unsubscribe(self._block_subscriber)
        for number, subscriber in self._humidifier_subscriber.items():
            self._humidifier[number].unsubscribe(subscriber)
        for number, subscriber in self._zone_subscriber.items():
            self._zone[number].unsubscribe(subscriber)
        self._close_all_valves()

    def _humidifier_changed(self, number, value):
        """Handle humidifier on/off."""
        if value:
            if self._zone[number].state:
                if self._loop_schedule:
                    _LOGGER.debug("Cancelling existing duty cycle schedule")
                    main_loop.remove_task(self._loop_schedule)
                _LOGGER.debug(
                    "Humidifier {} turned on, scheduling duty cycle start".format(
                        number
                    )
                )
                self._loop_schedule = main_loop.schedule_task(
                    lambda: self.start_cycle()
                )
            else:
                _LOGGER.debug(
                    "Humidifier {} turned on, but its zone is off".format(number)
                )
        else:
            if self._loop_schedule:
                _LOGGER.debug("Cancelling existing duty cycle schedule")
                main_loop.remove_task(self._loop_schedule)
            _LOGGER.debug(
                "Humidifier {} turned off, scheduling duty cycle stop".format(number)
            )
            self._loop_schedule = main_loop.schedule_task(lambda: self.stop_cycle())

    def _zone_changed(self, number, value):
        """Handle humidifier zone on/off."""
        if value:
            if self._pump_timeout is None:
                if self._loop_schedule:
                    _LOGGER.debug("Cancelling existing duty cycle schedule")
                    main_loop.remove_task(self._loop_schedule)
                _LOGGER.debug("Zone turned on, scheduling duty cycle start")
                self._loop_schedule = main_loop.schedule_task(
                    lambda: self.start_cycle()
                )
        elif all(not zone.state for zone in self._zone.values()):
            if self._loop_schedule:
                _LOGGER.debug("Cancelling existing duty cycle schedule")
                main_loop.remove_task(self._loop_schedule)
            _LOGGER.debug("All zones turned off, scheduling duty cycle stop")
            self._loop_schedule = main_loop.schedule_task(lambda: self.stop_cycle())

    def _pump_block_changed(self, value):
        """Handle block on/off."""
        if value:
            if self._loop_schedule:
                _LOGGER.debug("Cancelling existing duty cycle schedule")
                main_loop.remove_task(self._loop_schedule)
            _LOGGER.debug("Pump blocking turned on, scheduling duty cycle stop")
            self._loop_schedule = main_loop.schedule_task(lambda: self.stop_cycle())
        else:
            if self._loop_schedule:
                _LOGGER.debug("Cancelling existing duty cycle schedule")
                main_loop.remove_task(self._loop_schedule)
            _LOGGER.debug("Pump blocking turned off, scheduling duty cycle start")
            self._loop_schedule = main_loop.schedule_task(lambda: self.start_cycle())

    def _pump_changed(self, value):
        """Handle pump on/off."""
        if value and (
            self._pump_block.state
            or self._valve_switch[3].state
            or (
                not self._valve_switch[0].state
                and not self._valve_switch[1].state
                and not self._valve_switch[2].state
            )
        ):
            if self._loop_schedule:
                _LOGGER.debug("Cancelling existing duty cycle schedule")
                main_loop.remove_task(self._loop_schedule)
            _LOGGER.warning(
                "Stopping the pump because {}".format(
                    "blocked"
                    if self._pump_block.state
                    else (
                        "pressure drop valve open"
                        if self._valve_switch[3].state
                        else "all valves closed"
                    )
                )
            )
            self._loop_schedule = main_loop.schedule_task(lambda: self.stop_cycle())
            return

        if self._pump_timeout is not None:
            _LOGGER.debug("Cancelling existing pump timeout schedule")
            main_loop.remove_task(self._pump_timeout)
        if self._pressure_drop is not None:
            _LOGGER.debug("Cancelling pressure drop start")
            main_loop.remove_task(self._pressure_drop)
        if value and self._close_valves is not None:
            _LOGGER.debug("Cancelling pressure drop stop")
            main_loop.remove_task(self._close_valves)
            self._close_valves = None

        if value:
            _LOGGER.debug("Scheduling duty cycle stop after timeout")
            self._pump_timeout = main_loop.schedule_task(
                lambda: self._pump_on_timeout(),
                next_run=ticks_add(ticks_ms(), self._pump_on_timeout_ms),
            )
            self._pressure_drop = None
        else:
            _LOGGER.debug("Scheduling duty cycle start after timeout")
            self._pump_timeout = main_loop.schedule_task(
                lambda: self._pump_off_timeout(),
                next_run=ticks_add(ticks_ms(), self._pump_off_timeout_ms),
            )
            _LOGGER.debug("Scheduling pressure drop after timeout")
            self._pressure_drop = main_loop.schedule_task(
                lambda: self._start_pressure_drop(),
                next_run=ticks_add(ticks_ms(), self._pressure_drop_delay_ms),
            )

    def _pressure_drop_valve_changed(self, value):
        """Handle pressure drop valve on/off."""
        if self._pressure_drop is not None:
            _LOGGER.debug("Cancelling schedule for pressure drop cycle")
            main_loop.remove_task(self._pressure_drop)
            self._pressure_drop = None
        if self._close_valves is not None:
            _LOGGER.debug("Cancelling existing schedule to close all valves")
            main_loop.remove_task(self._close_valves)

        if value:
            _LOGGER.debug("Pressure drop valve opened, scheduling closing all valves")
            self._close_valves = main_loop.schedule_task(
                lambda: self._close_all_valves(),
                next_run=ticks_add(ticks_ms(), self._pressure_drop_time_ms),
            )
        else:
            self._close_valves = None

    def _start_pressure_drop(self):
        """Initiate pressure drop."""
        _LOGGER.debug("Opening pressure drop valve")
        self._valve_switch[3].state = True

    def _close_all_valves(self):
        """Complete pressure drop."""
        _LOGGER.debug("Closing all valves")
        for switch in self._valve_switch.values():
            switch.state = False

    def _pump_on_timeout(self):
        """Handle pump staying on too long."""
        if self._pump_timeout is not None:
            _LOGGER.debug("Pump timeout, cancelling it")
            main_loop.remove_task(self._pump_timeout)
            self._pump_timeout = None
        _LOGGER.debug("Stopping the cycle")
        self.stop_cycle()

    def _pump_off_timeout(self):
        """Handle pump staying off too long."""
        if self._pump_timeout is not None:
            _LOGGER.debug("Pump timeout, cancelling it")
            main_loop.remove_task(self._pump_timeout)
            self._pump_timeout = None
        _LOGGER.debug("Starting the cycle")
        self.start_cycle()

    def stop_cycle(self):
        """End duty cycle."""
        main_loop.remove_task(self._loop_schedule)
        self._loop_schedule = None

        if not self._pump.state:
            _LOGGER.debug("The pump is already not running")
            return

        _LOGGER.debug("Stopping the pump")
        self._pump.state = False

    def start_cycle(self):
        """Enter duty cycle."""
        main_loop.remove_task(self._loop_schedule)
        self._loop_schedule = None

        if self._pump.state:
            _LOGGER.debug("The pump is already running")
            return

        if self._pump_block.state:
            _LOGGER.debug("Pump start blocked")
            return

        if (
            not self._zone[0].state
            and not self._zone[1].state
            and not self._zone[2].state
        ):
            _LOGGER.debug("All zones are off, not starting the pump")
            return

        _LOGGER.debug("Setting up switches")
        for x in range(3):
            self._valve_switch[x].state = self._zone[x].state
        self._valve_switch[3].state = False

        _LOGGER.debug("Starting the pump")
        self._pump.state = True
