"""Test xbee_humidifier."""
import asyncio
import json
import threading
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import callback
from homeassistant.exceptions import ServiceNotFound

from custom_components.xbee_humidifier.coordinator import XBeeHumidifierApiClient

from .conftest import commands
from .const import IEEE


def test_double_start(hass):
    """Test api client does not double init."""

    client = XBeeHumidifierApiClient(hass, IEEE)

    listener = client._remove_listener
    assert listener is not None

    client.start()
    assert client._remove_listener == listener


async def test_synchronous_command(hass, data_from_device):
    """Test synchronous command call."""

    client = XBeeHumidifierApiClient(hass, IEEE)

    with pytest.raises(
        NotImplementedError,
        match="The synchronous function cannot be run from the main hass loop, "
        "run from thread instead or use async version",
    ):
        client.command("bind")

    result = {}

    def thread_function(cmd):
        result[cmd] = client.command(cmd)

    x = threading.Thread(target=thread_function, args=("bind",))
    x.start()
    while x.is_alive():
        await hass.async_block_till_done()
        x.join(timeout=0.001)
    assert result["bind"] == "OK"


async def test_asynchronous_command(hass, data_from_device):
    """Test asynchronous command call."""

    client = XBeeHumidifierApiClient(hass, IEEE)

    # No args
    assert await client.async_command("bind") == "OK"
    # One arg
    assert await client.async_command("mode", 0) == "normal"
    # Two args
    commands["target_hum"].return_value = "OK"
    assert await client.async_command("target_hum", 1, 55) == "OK"
    # With kwargs
    assert not await client.async_command("hum", number=2)
    # Both args and kwargs
    commands["valve"].return_value = "OK"
    assert await client.async_command("valve", 3, state=True) == "OK"


async def test_double_command(hass, data_from_device):
    """Test executing two commands of the same name at once."""

    client = XBeeHumidifierApiClient(hass, IEEE)

    assert await asyncio.gather(
        client.async_command("valve", number=0), client.async_command("valve", number=1)
    ) == [False, False]


async def test_unexpected_command_response(hass):
    """Test receiving unexpected command response."""

    def data_from_device(hass, ieee, data):
        """Simulate receiving data from device."""
        hass.bus.async_fire(
            "zha_event",
            {
                "device_ieee": ieee,
                "unique_id": ieee + ":232:0x0008",
                "device_id": "abcdef01234567899876543210fedcba",
                "endpoint_id": 232,
                "cluster_id": 8,
                "command": "receive_data",
                "args": {"data": json.dumps(data)},
            },
        )

    client = XBeeHumidifierApiClient(hass, IEEE)  # noqa: F841

    data_from_device(hass, IEEE, {"test_resp": "Passed"})


async def test_unexpected_command_error(hass):
    """Test receiving command error response."""

    def data_from_device(hass, ieee, data):
        """Simulate receiving data from device."""
        hass.bus.async_fire(
            "zha_event",
            {
                "device_ieee": ieee,
                "unique_id": ieee + ":232:0x0008",
                "device_id": "abcdef01234567899876543210fedcba",
                "endpoint_id": 232,
                "cluster_id": 8,
                "command": "receive_data",
                "args": {"data": json.dumps(data)},
            },
        )

    @callback
    def respond(call):
        data_from_device(hass, call.data["ieee"], {"bind_resp": {"err": "Test error"}})

    hass.services.async_register("zha", "issue_zigbee_cluster_command", respond)

    client = XBeeHumidifierApiClient(hass, IEEE)

    with pytest.raises(RuntimeError, match="Command response: Test error"):
        await client.async_command("bind")

    hass.services.async_remove("zha", "issue_zigbee_cluster_command")


async def test_subscribers(hass, caplog, data_from_device):
    """Test data receive callbacks."""

    client = XBeeHumidifierApiClient(hass, IEEE)

    listener = AsyncMock()
    listener_all = AsyncMock()
    client.add_subscriber("test_data", listener)
    client.add_subscriber("data_received", listener_all)

    data_from_device(hass, IEEE, {"test_data": "test_value"})
    data_from_device(hass, IEEE, {"test_data2": "test_value2"})
    await hass.async_block_till_done()

    listener.assert_awaited_once_with("test_value")
    assert listener_all.await_count == 2
    assert listener_all.await_args_list[0][0][0] == {"test_data": "test_value"}
    assert listener_all.await_args_list[1][0][0] == {"test_data2": "test_value2"}
    assert "No callback for {'test_data2': 'test_value2'}" in caplog.text


@patch("custom_components.xbee_humidifier.coordinator.XBeeHumidifierApiClient._cmd")
async def test_timeout(cmd_mock, hass):
    """Test data receive timeout."""

    client = XBeeHumidifierApiClient(hass, IEEE)

    cmd_mock.side_effect = TimeoutError

    with pytest.raises(TimeoutError, match="No response to bind command"):
        await client.async_command("bind", retry_count=7)

    assert cmd_mock.call_count == 7


@patch("custom_components.xbee_humidifier.coordinator.XBeeHumidifierApiClient._cmd")
async def test_remote_buffer_full(cmd_mock, hass):
    """Test retry on remote buffer full."""

    from zigpy.exceptions import DeliveryError

    client = XBeeHumidifierApiClient(hass, IEEE)

    cmd_mock.side_effect = DeliveryError("Failed to deliver packet")

    with pytest.raises(DeliveryError, match="Failed to deliver packet"):
        await client.async_command("bind", retry_count=3)

    assert cmd_mock.call_count == 3


async def test_service_call_exception(hass):
    """Test service call exception."""

    client = XBeeHumidifierApiClient(hass, IEEE)

    with pytest.raises(ServiceNotFound, match="service_not_found"):
        await client.async_command("bind")
