"""Tests for xbee_humidifier."""

import sys
from unittest.mock import patch

sys.path.append("tests/modules")
sys.path.append("flash")
sys.modules["time"] = __import__("mock_time")

with patch("lib.mainloop.main_loop.run"):
    import flash  # noqa: F401
