"""Tests for xbee_humidifier."""

import sys

sys.path.append("tests/modules")
sys.path.append("flash")
sys.modules["time"] = __import__("mock_time")
sys.modules["gc"] = __import__("mock_gc")
