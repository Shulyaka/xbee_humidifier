"""Test config."""

import sys

sys.path.append("flash/lib")
from core import Entity  # noqa: E402

from flash import config  # noqa: E402


def test_config():
    """Test config."""
    assert isinstance(config.pump, Entity)
    assert isinstance(config.valve_switch, dict)
    assert len(config.valve_switch) == 4
    for x in range(4):
        assert isinstance(config.valve_switch[x], Entity)
