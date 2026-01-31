"""Simple main loop implementation."""

from gc import collect
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

from lib import logging

_LOGGER = logging.getLogger(__name__)


class Task:
    """Class representing the task."""

    def __init__(self, callback, next_run=None, period=None):
        """Init the class."""
        self._callback = callback
        self._period = period
        if next_run is None:
            self._next_run = ticks_ms()
        else:
            self._next_run = ticks_add(ticks_ms(), next_run)

    def run(self):
        """Execute the task and return the next scheduled time."""
        try:
            collect()
            self._callback()
        except Exception as e:
            _LOGGER.error("mainloop: error with {}".format(self._callback))
            _LOGGER.error("{}: {}".format(type(e).__name__, e))

        if self._period:
            self._next_run = ticks_add(self._next_run, self._period)
            now = ticks_ms()
            if ticks_diff(self._next_run, now) < 0:
                self._next_run = ticks_add(now, self._period)
            collect()
            return self._next_run

        self._callback = None
        collect()
        return None

    @property
    def next_run(self):
        """Return the time of the next scheduled execution or None if completed."""
        if self._callback is None:
            return None
        return self._next_run


class Loop:
    """Event loop."""

    def __init__(self):
        """Init the class."""
        self._last_run = None
        self._tasks = []
        self._atexit = []
        self._stop = False
        self._task_scheduled = False

    def schedule_task(self, *args, **kwargs):
        """Add new task."""
        collect()
        task = Task(*args, **kwargs)
        self._tasks.append(task)
        self._task_scheduled = True
        collect()
        return task

    def remove_task(self, task):
        """Remove task if scheduled."""
        if task is not None and task in self._tasks:
            self._tasks.remove(task)
            collect()

    def reset(self):
        """Remove all tasks."""
        self._tasks.clear()
        self._atexit.clear()
        collect()

    def atexit(self, callback):
        """Register a callback to be called on system shutdown."""
        self._atexit.append(callback)
        collect()
        return callback

    def remove_atexit(self, callback):
        """Remove a registered atexit callback."""
        if callback in self._atexit:
            self._atexit.remove(callback)
            collect()

    def run_once(self):
        """Run one iteration and return the time of next execution."""
        collect()
        next_time = None
        self._task_scheduled = False

        for task in self._tasks.copy():
            if task not in self._tasks:
                continue
            next_run = task.next_run
            if next_run is not None and ticks_diff(next_run, ticks_ms()) <= 0:
                next_run = task.run()

            if next_run is None and task in self._tasks:
                self._tasks.remove(task)
                collect()

            if next_run is not None and (
                next_time is None or ticks_diff(next_run, next_time) < 0
            ):
                next_time = next_run

        if self._task_scheduled:
            next_time = self.next_run
            self._task_scheduled = False

        collect()
        return next_time

    def run(self):
        """Run the loop continuously."""
        collect()
        try:
            self._stop = False
            while not self._stop:
                next_time = self.run_once()
                now = ticks_ms()
                if next_time is None:
                    if self._stop:
                        return None
                    raise RuntimeError("No tasks")
                diff = ticks_diff(next_time, now)
                if diff > 0 and not self._stop:
                    sleep_ms(diff)
        except SystemExit as e:
            _LOGGER.info("mainloop: SystemExit: {}".format(e))
            self._tasks.clear()
            for c in self._atexit:
                self.schedule_task(c)
            self._atexit.clear()
            now = ticks_ms()
            next_time = now
            while next_time is not None and ticks_diff(next_time, now) <= 0:
                next_time = self.run_once()
            self._tasks.clear()
            collect()
            raise
        collect()
        return next_time

    @property
    def next_run(self):
        """Return the time of the next scheduled execution."""
        now = ticks_ms()
        next_time = None

        for task in self._tasks:
            next_run = task.next_run
            if ticks_diff(next_run, now) <= 0:
                return now

            if next_run is not None and (
                next_time is None or ticks_diff(next_run, next_time) < 0
            ):
                next_time = next_run

        return next_time

    def stop(self):
        """Stop the loop after current iteration."""
        self._stop = True


main_loop = Loop()
