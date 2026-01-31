"""Test main."""

from unittest import mock

import pytest
from lib import mainloop


def test_main(caplog):
    """Test the main code."""
    mainloop.main_loop.run = mock.MagicMock(
        side_effect=RuntimeError("Test mainloop exception")
    )
    with (
        mock.patch.dict("sys.modules", {"bundle": None}),
        pytest.raises(RuntimeError) as excinfo,
    ):
        import main  # noqa: F401

    mainloop.main_loop.run.assert_called_once_with()
    assert "Test mainloop exception" in caplog.text
    assert "Mainloop exited" in caplog.text
    assert "Test mainloop exception" in str(excinfo.value)
