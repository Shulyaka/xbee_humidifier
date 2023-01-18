"""Tests for xbee_humidifier."""

import sys

sys.path.append("tests/modules")
sys.path.append("flash")
sys.path.append("flash/lib")
sys.modules["time"] = __import__("mock_time")
