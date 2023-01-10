"""Simple main loop implementation."""

import logging
from time import ticks_ms, sleep_ms

_LOGGER = logging.getLogger(__name__)


class Task:
    def __init__(self, callback, next_run=None, period=None):
        self._callback = callback
        self._next_run = next_run
        self._period = period

        if self._next_run is None and self._period is not None:
            self._next_run = ticks_ms() + self._period

    def run(self):
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
        return self._next_run if self._next_run is not None else ticks_ms()

    @property
    def completed(self):
        return True if self._callback is None else False


class Loop:
    _last_run = None
    _tasks = []
    _stop = False

    def schedule_task(self, callback, next_run=None, period=None):
        new_task = Task(callback, next_run, period)
        self._tasks.append(new_task)
        return lambda: self._tasks.remove(new_task)

    def reset(self):
        self._tasks.clear()

    def run_once(self):
        now = ticks_ms()
        next_time = None

        for task in self._tasks:
            next_run = task.next_run
            if next_run <= now:
                task.run()
                if task.completed:
                    self._tasks.remove(task)
                    next_run = None
                else:
                    next_run = task.next_run

            if next_run is not None and (next_time is None or next_run - next_time < 0):
                next_time = next_run

        return next_time

    def run(self):
        while not self._stop:
            next_time = self.run_once()
            now = ticks_ms()
            if next_time is None:
                _LOGGER.warning("No tasks")
                next_time = now + 1000
            diff = next_time - now
            if diff > 0:
                sleep_ms(diff)
        self._stop = False

    def stop(self):
        self._stop = True


main_loop = Loop()
