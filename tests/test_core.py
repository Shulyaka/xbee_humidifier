"""Test core lib."""

from unittest import mock

import pytest
from lib import core


def test_subscription(caplog):
    """Test Sensor class subscriptions."""
    entity = core.Sensor()
    assert entity._triggers == []

    callback = mock.MagicMock()
    unsubscribe = entity.subscribe(callback)
    entity.state = 42

    callback.assert_called_once_with(42)

    callback.reset_mock()
    entity.unsubscribe(unsubscribe)
    assert entity._triggers == []

    entity.state = 21
    assert callback.call_count == 0

    with pytest.raises(ValueError) as excinfo:
        entity.unsubscribe(unsubscribe)

    assert str(excinfo.value) == "list.remove(x): x not in list"

    def callback_exception(value):
        raise RuntimeError("Test callback exception")

    entity.subscribe(callback_exception)
    entity.state = 84

    assert "Test callback exception" in caplog.text


def test_virtual_switch():
    """Test Switch class."""

    assert not core.Switch().state
    assert core.Switch(True).state
    assert not core.Switch(False).state
    assert core.Switch(1).state
    assert core.Switch(3).state

    switch = core.Switch(False)

    callback = mock.MagicMock()
    switch.subscribe(callback)

    switch.state = True
    assert switch.state
    callback.assert_called_once_with(True)


def test_virtual_sensor():
    """Test Sensor class."""

    assert core.Sensor().state is None
    assert core.Sensor(True).state
    assert not core.Sensor(False).state
    assert core.Sensor(1).state == 1
    assert core.Sensor(3).state == 3

    sensor = core.Sensor(0)

    callback = mock.MagicMock()
    sensor.subscribe(callback)

    sensor.state = 123
    assert sensor.state == 123
    callback.assert_called_once_with(123)
