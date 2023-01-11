"""Test mainloop lib."""

import sys
from unittest import mock

sys.path.append("tests/modules")
sys.modules["time"] = __import__("mock_time")

from time import sleep_ms as mock_sleep_ms, ticks_ms as mock_ticks_ms  # noqa: E402

import flash.lib.mainloop  # noqa: E402


def test_task():
    """Test Task class."""
    callback = mock.MagicMock()
    mock_ticks_ms.return_value = 1000
    task = flash.lib.mainloop.Task(callback)
    assert task.next_run == 1000
    assert not task.completed
    mock_ticks_ms.return_value = 1005
    assert task.next_run == 1005

    task.run()
    callback.assert_called_once_with()
    assert task.completed

    assert flash.lib.mainloop.Task(callback, next_run=1050).next_run == 1050
    assert flash.lib.mainloop.Task(callback, period=100).next_run == 1105

    task = flash.lib.mainloop.Task(callback, next_run=1050, period=100)
    task.run()
    assert not task.completed
    assert task.next_run == 1150

    mock_ticks_ms.return_value = 2000
    task.run()
    assert task.next_run == 2100


def test_loop():
    """Test Loop class."""
    callback = mock.MagicMock()
    mock_ticks_ms.return_value = 1000

    loop = flash.lib.mainloop.Loop()
    assert loop.run_once() is None

    delete_task = loop.schedule_task(callback)
    assert loop.run_once() is None
    delete_task()
    delete_task()
    callback.assert_called_once_with()

    callback.reset_mock()
    callback2 = mock.MagicMock()
    loop.schedule_task(callback, next_run=1100)
    loop.schedule_task(callback2, next_run=1200)
    assert loop.run_once() == 1100
    assert callback.call_count == 0
    assert callback2.call_count == 0
    mock_ticks_ms.return_value = 1105
    assert loop.run_once() == 1200
    callback.assert_called_once_with()
    assert callback2.call_count == 0
    mock_ticks_ms.return_value = 1200
    assert loop.run_once() is None
    callback2.assert_called_once_with()

    callback.reset_mock()
    loop.schedule_task(callback, period=100)
    loop.reset()
    assert loop.run_once() is None
    assert callback.call_count == 0

    loop.schedule_task(callback)
    loop.schedule_task(lambda: loop.stop())
    assert loop.run() == 2200
    callback.assert_called_once_with()
    assert mock_sleep_ms.call_count == 0

    assert loop != flash.lib.mainloop.main_loop
