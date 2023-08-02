"""The micropython module to run the tests."""

from unittest.mock import MagicMock


def const(x):
    """Return same value."""
    return x


kbd_intr = MagicMock()
mem_info = MagicMock()
opt_level = MagicMock()
