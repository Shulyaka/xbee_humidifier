"""Test core lib."""

from unittest import mock

import pytest

import flash.lib.core


def test_entity():
    """Test Entity class."""
    entity = flash.lib.core.Entity()
    assert entity._triggers == []

    callback = mock.MagicMock()
    unsubscribe = entity.subscribe(callback)
    entity.state = 42

    callback.assert_called_once_with(42)

    callback.reset_mock()
    unsubscribe()
    assert entity._triggers == []

    entity.state = 21
    callback.assert_not_called()

    with pytest.raises(ValueError) as excinfo:
        unsubscribe()

    assert str(excinfo.value) == "list.remove(x): x not in list"


def test_virtual_switch():
    """Test VirtualSwitch class."""

    assert not flash.lib.core.VirtualSwitch().state
    assert flash.lib.core.VirtualSwitch(True).state
    assert not flash.lib.core.VirtualSwitch(False).state
    assert flash.lib.core.VirtualSwitch(1).state
    assert flash.lib.core.VirtualSwitch(3).state

    switch = flash.lib.core.VirtualSwitch(False)

    callback = mock.MagicMock()
    switch.subscribe(callback)

    switch.state = True
    assert switch.state
    callback.assert_called_once_with(True)


def test_virtual_sensor():
    """Test VirtualSensor class."""

    assert flash.lib.core.VirtualSensor().state is None
    assert flash.lib.core.VirtualSensor(True).state
    assert not flash.lib.core.VirtualSensor(False).state
    assert flash.lib.core.VirtualSensor(1).state == 1
    assert flash.lib.core.VirtualSensor(3).state == 3

    sensor = flash.lib.core.VirtualSensor(0)

    callback = mock.MagicMock()
    sensor.subscribe(callback)

    sensor.state = 123
    assert sensor.state == 123
    callback.assert_called_once_with(123)
