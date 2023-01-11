"""The time mock module to run the tests."""

from unittest.mock import MagicMock

sleep = MagicMock()
ticks_ms = MagicMock(return_value=0)
