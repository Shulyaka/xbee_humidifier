"""Test main."""

from unittest import mock

from lib import mainloop


def test_main(caplog):
    """Test the main code."""
    mainloop.main_loop.run = mock.MagicMock(
        side_effect=RuntimeError("Test mainloop exception")
    )
    with mock.patch.dict("sys.modules", {"bundle": None}):
        import main
    main.main_loop.run.assert_called_once_with()
    assert "Test mainloop exception" in caplog.text
    assert "Mainloop exited" in caplog.text
