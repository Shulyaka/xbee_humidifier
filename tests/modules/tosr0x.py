"""The tosr0x module to run the tests."""

from unittest.mock import MagicMock, PropertyMock

mock_tosr = MagicMock()

mock_temperature = PropertyMock(return_value=0)
type(mock_tosr).temperature = mock_temperature
mock_temperature.return_value = 42
mock_tosr.get_relay_state.return_value = True

tosr0x_version = MagicMock()
tosr0x_version.return_value = None


def Tosr0x():
    """Fake Tosr0x class constructor returning MagickMock instead."""
    return mock_tosr
