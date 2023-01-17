"""Simple main loop implementation."""

import logging
from time import sleep_ms, ticks_ms

_LOGGER = logging.getLogger(__name__)


class Task:
    """Class representing the task."""

    def __init__(self, callback, next_run=None, period=None):
        """Init the class."""
        self._callback = callback
        self._next_run = next_run
        self._period = period

        if self._next_run is None and self._period is not None:
            self._next_run = ticks_ms() + self._period

    def run(self):
        """Execute the task."""
        try:
            self._callback()
        except Exception as e:
            _LOGGER.error(e)

        if self._period:
            self._next_run += self._period
            now = ticks_ms()
            if self._next_run - now < 0:
                self._next_run = now + self._period
        else:
            self._callback = None

    @property
    def next_run(self):
        """Return the time of the next scheduled execution."""
        return self._next_run if self._next_run is not None else ticks_ms()

    @property
    def completed(self):
        """Return whether the task is complete or not."""
        return True if self._callback is None else False


class Loop:
    """Event loop."""

    _last_run = None
    _tasks = []
    _stop = False

    def schedule_task(self, callback, next_run=None, period=None):
        """Add new task."""
        new_task = Task(callback, next_run, period)
        self._tasks.append(new_task)
        return lambda: self._tasks.remove(new_task) if new_task in self._tasks else None

    def reset(self):
        """Remove all tasks."""
        self._tasks.clear()

    def run_once(self):
        """Run one iteration and return the time of next eecution."""
        now = ticks_ms()
        next_time = None

        tasks = self._tasks.copy()
        for task in tasks:
            next_run = task.next_run
            if next_run - now <= 0:
                task.run()
                if task.completed:
                    if task in self._tasks:
                        self._tasks.remove(task)
                    next_run = None
                else:
                    next_run = task.next_run

            if next_run is not None and (next_time is None or next_run - next_time < 0):
                next_time = next_run

        return next_time

    def run(self):
        """Run the loop continuously."""
        while not self._stop:
            next_time = self.run_once()
            now = ticks_ms()
            if next_time is None:
                _LOGGER.warning("No tasks")
                next_time = now + 1000
            diff = next_time - now
            if diff > 0 and not self._stop:
                sleep_ms(diff)
        self._stop = False
        return next_time

    @property
    def next_run(self):
        """Return the time of the next scheduled execution."""
        now = ticks_ms()
        next_time = None

        for task in self._tasks:
            next_run = task.next_run
            if next_run <= now:
                return now

            if next_time is None or next_run - next_time < 0:
                next_time = next_run

        return next_time

    def stop(self):
        """Exit the loop after current iteration."""
        self._stop = True


main_loop = Loop()
