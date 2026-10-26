"""Tests for xbee_humidifier."""

import sys
from collections.abc import Iterator
from contextlib import contextmanager

from pytest import MonkeyPatch

sys.path = ["tests/modules", "flash"] + sys.path


@contextmanager
def mock_micropython() -> Iterator[None]:
    """Supply MicroPython mocks only while importing firmware modules."""
    with MonkeyPatch.context() as monkeypatch:
        monkeypatch.setitem(sys.modules, "time", __import__("mock_time"))
        monkeypatch.setitem(sys.modules, "gc", __import__("mock_gc"))
        yield
