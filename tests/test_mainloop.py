"""Test mainloop lib."""

from time import sleep_ms as mock_sleep_ms, ticks_ms as mock_ticks_ms
from unittest import mock

import pytest
from lib import mainloop


def test_task():
    """Test Task class."""
    # Test task next_run after creation
    callback = mock.MagicMock()
    mock_ticks_ms.return_value = 1000
    task = mainloop.Task(callback)
    assert task.next_run == 1000

    # Test task next_run after completion
    next_run = task.run()
    callback.assert_called_once_with()
    assert next_run is None
    assert task.next_run is None

    # Test task next_run for periodic tasks
    assert mainloop.Task(callback, next_run=50).next_run == 1050
    assert mainloop.Task(callback, period=100).next_run == 1000

    # Test task next_run after completion of a periodic task
    task = mainloop.Task(callback, next_run=50, period=100)
    next_run = task.run()
    assert next_run == 1150
    assert task.next_run == 1150

    # Test task next_run after a missed period (sic!)
    mock_ticks_ms.return_value = 2000
    next_run = task.run()
    assert next_run == 2100
    assert task.next_run == 2100


def test_loop():
    """Test Loop class."""
    callback = mock.MagicMock()
    mock_ticks_ms.return_value = 1000
    mock_sleep_ms.reset_mock()

    # Test empty loop
    loop = mainloop.Loop()
    assert loop.next_run is None
    assert loop.run_once() is None
    with pytest.raises(RuntimeError) as excinfo:
        loop.run()
    assert "No tasks" in str(excinfo.value)

    # Test mainloop with a single task
    delete_task = loop.schedule_task(callback)
    assert loop.next_run == 1000
    assert loop.run_once() is None
    assert loop.next_run is None
    loop.remove_task(delete_task)
    loop.remove_task(delete_task)
    callback.assert_called_once_with()

    # Test mainloop with two tasks
    callback.reset_mock()
    callback2 = mock.MagicMock()
    loop.schedule_task(callback, next_run=100)
    loop.schedule_task(callback2, next_run=200)
    assert loop.next_run == 1100
    assert loop.run_once() == 1100
    assert callback.call_count == 0
    assert callback2.call_count == 0
    mock_ticks_ms.return_value = 1105
    assert loop.next_run == 1105
    assert loop.run_once() == 1200
    assert loop.next_run == 1200
    callback.assert_called_once_with()
    assert callback2.call_count == 0
    mock_ticks_ms.return_value = 1200
    assert loop.next_run == 1200
    assert loop.run_once() is None
    callback2.assert_called_once_with()

    # Test mainloop reset
    callback.reset_mock()
    loop.schedule_task(callback, period=100)
    loop.reset()
    mock_ticks_ms.return_value = 1300
    assert loop.next_run is None
    assert loop.run_once() is None
    assert callback.call_count == 0

    # Test mainloop stop
    loop.schedule_task(callback)
    loop.schedule_task(lambda: loop.stop())
    assert loop.run() is None
    assert loop.next_run is None
    callback.assert_called_once_with()
    assert mock_sleep_ms.call_count == 0

    # Test mainloop sleep
    loop.schedule_task(lambda: loop.stop(), next_run=100)
    assert loop.run() is None
    assert loop.next_run is None
    mock_sleep_ms.assert_called_once_with(100)

    # Test task scheduling from within the loop
    mock_sleep_ms.reset_mock()
    callback.reset_mock()
    loop.schedule_task(lambda: loop.schedule_task(callback))
    loop.schedule_task(lambda: loop.schedule_task(lambda: loop.stop()))
    assert loop.run() is None
    assert loop.next_run is None
    callback.assert_called_once_with()
    assert mock_sleep_ms.call_count == 0

    # Test task removal from within the loop
    callback.reset_mock()
    task = None
    loop.schedule_task(lambda: loop.remove_task(task))
    task = loop.schedule_task(callback)
    assert loop.run_once() is None
    assert loop.next_run is None
    assert callback.call_count == 0

    # Test task remaining after stop
    callback.reset_mock()
    task = loop.schedule_task(callback, next_run=100, period=100)
    loop.schedule_task(lambda: loop.schedule_task(lambda: loop.stop()))
    assert loop.run() == 1500
    assert loop.next_run == 1500
    assert callback.call_count == 0
    assert mock_sleep_ms.call_count == 0
    loop.remove_task(task)
    assert loop.next_run is None

    # Test mainloop with periodic task
    callback.reset_mock()
    task = loop.schedule_task(callback, period=100)
    mock_ticks_ms.return_value = 2300
    assert loop.run_once() == 2400
    assert callback.call_count == 1

    mock_ticks_ms.return_value = 2400
    assert loop.run_once() == 2500
    assert callback.call_count == 2

    mock_ticks_ms.return_value = 2500
    assert loop.run_once() == 2600
    assert callback.call_count == 3

    loop.remove_task(task)
    assert loop.next_run is None

    # Test task scheduling for the next iteration
    callback.reset_mock()
    loop.schedule_task(lambda: loop.schedule_task(callback))
    assert loop.run_once() == 2500
    assert callback.call_count == 0
    assert loop.run_once() is None
    assert callback.call_count == 1

    # Test callback with exception does not break the loop
    callback.reset_mock()
    callback.side_effect = RuntimeError("Test exception in callback")
    loop.schedule_task(callback)
    assert loop.run_once() is None
    assert callback.call_count == 1
