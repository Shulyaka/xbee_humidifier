"""Test __init__."""

from tests import mock_micropython

with mock_micropython():
    import flash


def test_init():
    """Test the main code."""
    assert not hasattr(flash, "setup")
