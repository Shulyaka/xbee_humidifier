"""Test core lib."""

from unittest import mock

import pytest

from flash.lib import core


def test_entity():
    """Test Entity class."""
    entity = core.Entity()
    assert entity._triggers == []

    callback = mock.MagicMock()
    unsubscribe = entity.subscribe(callback)
    entity.state = 42

    callback.assert_called_once_with(42)

    callback.reset_mock()
    unsubscribe()
    assert entity._triggers == []

    entity.state = 21
    assert callback.call_count == 0

    with pytest.raises(ValueError) as excinfo:
        unsubscribe()

    assert str(excinfo.value) == "list.remove(x): x not in list"


def test_virtual_switch():
    """Test VirtualSwitch class."""

    assert not core.VirtualSwitch().state
    assert core.VirtualSwitch(True).state
    assert not core.VirtualSwitch(False).state
    assert core.VirtualSwitch(1).state
    assert core.VirtualSwitch(3).state

    switch = core.VirtualSwitch(False)

    callback = mock.MagicMock()
    switch.subscribe(callback)

    switch.state = True
    assert switch.state
    callback.assert_called_once_with(True)


def test_virtual_sensor():
    """Test VirtualSensor class."""

    assert core.VirtualSensor().state is None
    assert core.VirtualSensor(True).state
    assert not core.VirtualSensor(False).state
    assert core.VirtualSensor(1).state == 1
    assert core.VirtualSensor(3).state == 3

    sensor = core.VirtualSensor(0)

    callback = mock.MagicMock()
    sensor.subscribe(callback)

    sensor.state = 123
    assert sensor.state == 123
    callback.assert_called_once_with(123)
