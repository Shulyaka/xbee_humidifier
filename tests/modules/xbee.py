"""The xbee module to run the tests."""

from unittest.mock import MagicMock

ADDR_COORDINATOR = b"\x00\x00\x00\x00\x00\x00\x00\x00"

transmit = MagicMock()
