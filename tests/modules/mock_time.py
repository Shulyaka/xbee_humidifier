"""The time mock module to run the tests."""

from unittest.mock import MagicMock

ticks_ms = MagicMock(return_value=0)


def _time_pass(t):
    ticks_ms.return_value += t


sleep_ms = MagicMock(side_effect=_time_pass)
sleep = MagicMock(side_effect=lambda x: _time_pass(x * 1000))
