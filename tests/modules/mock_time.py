"""The time mock module to run the tests."""

from unittest.mock import MagicMock

ticks_ms = MagicMock(return_value=0)


def _time_pass(t):
    ticks_ms.return_value += t


sleep_ms = MagicMock(side_effect=_time_pass)
sleep = MagicMock(side_effect=lambda x: _time_pass(x * 1000))


def ticks_add(ticks, delta):
    """Offset ticks value by a given number."""
    return ticks + delta


def ticks_diff(ticks1, ticks2):
    """Measure ticks difference between values."""
    return ticks1 - ticks2
