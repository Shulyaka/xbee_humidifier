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
        self._next_run = next_run
        self._period = period

        if self._next_run is None and self._period is not None:
            self._next_run = ticks_add(ticks_ms(), self._period)

    def run(self):
        """Execute the task."""
        try:
            self._callback()
        except Exception as e:
            _LOGGER.error("mainloop: error with %s", self._callback)
            _LOGGER.error(type(e).__name__ + ": " + str(e))

        if self._period:
            self._next_run = ticks_add(self._next_run, self._period)
            now = ticks_ms()
            if ticks_diff(self._next_run, now) < 0:
                self._next_run = ticks_add(now, self._period)
        else:
            self._callback = None

        collect()

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

    def __init__(self):
        """Init the class."""
        self._last_run = None
        self._tasks = []
        self._stop = False
        self._run_time = 0
        self._idle_time = 0
        self._task_scheduled = False

    def schedule_task(self, callback, *args, **kwargs):
        """Add new task."""
        new_task = Task(callback, *args, **kwargs)
        self._tasks.append(new_task)
        self._task_scheduled = True
        return lambda: self._tasks.remove(new_task) if new_task in self._tasks else None

    def reset(self):
        """Remove all tasks."""
        self._tasks.clear()

    def run_once(self):
        """Run one iteration and return the time of next execution."""
        next_time = None
        self._task_scheduled = False

        for task in self._tasks.copy():
            if task not in self._tasks:
                continue
            next_run = task.next_run
            if ticks_diff(next_run, ticks_ms()) <= 0:
                task.run()
                if task.completed:
                    if task in self._tasks:
                        self._tasks.remove(task)
                    next_run = None
                else:
                    next_run = task.next_run

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
        self._stop = False
        while not self._stop:
            start = ticks_ms()
            next_time = self.run_once()
            now = ticks_ms()
            self._run_time += ticks_diff(now, start)
            if next_time is None:
                if self._stop:
                    return None
                raise RuntimeError("No tasks")
            diff = ticks_diff(next_time, now)
            if diff > 0 and not self._stop:
                self._idle_time += diff
                sleep_ms(diff)
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

            if next_time is None or ticks_diff(next_run, next_time) < 0:
                next_time = next_run

        return next_time

    def stop(self):
        """Exit the loop after current iteration."""
        self._stop = True


main_loop = Loop()
