"""The xbee module to run the tests."""

from unittest.mock import MagicMock

ADDR_COORDINATOR = b"\x00\x00\x00\x00\x00\x00\x00\x00"

atcmd = MagicMock(return_value="OK")
transmit = MagicMock()
receive = MagicMock()


def _receive_once(*args, **kwargs):
    """Make the receive mock return the value only once."""
    ret = receive.return_value
    receive.return_value = None
    return ret  # noqa: R504


receive.return_value = None
receive.side_effect = _receive_once
