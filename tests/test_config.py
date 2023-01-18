"""Test config."""

import sys
from unittest.mock import patch

sys.path.append("tests/modules")
sys.path.append("flash")
sys.path.append("flash/lib")
sys.modules["time"] = __import__("mock_time")

from core import Entity  # noqa: E402

with patch("flash.lib.tosr0x.stdout.buffer.write") as mock_stdout:
    with patch("flash.lib.tosr0x.stdin.buffer.read") as mock_stdin:
        from flash import config


def test_config():
    """Test config."""
    assert isinstance(config.debug, bool)
    assert isinstance(config.pump, Entity)
    assert isinstance(config.pressure_in, Entity)
    assert isinstance(config.pressure_out, Entity)
    assert isinstance(config.valve_switch, dict)
    assert len(config.valve_switch) == 4
    for x in range(4):
        assert isinstance(config.valve_switch[x], Entity)
