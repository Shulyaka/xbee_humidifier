"""Test cancellation of callers waiting for device commands."""

import asyncio
import gc
import json
import weakref
from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant, ServiceCall, callback

from custom_components.xbee_humidifier.coordinator import XBeeHumidifierApiClient

from .const import IEEE


@pytest.fixture
async def client(hass: HomeAssistant) -> AsyncIterator[XBeeHumidifierApiClient]:
    """Create a client and finish any workers left by a failed test."""
    api_client = XBeeHumidifierApiClient(hass, IEEE)
    yield api_client
    api_client.stop()
    tasks = tuple(api_client._command_tasks)
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


@pytest.fixture
def sent_commands(
    hass: HomeAssistant,
) -> Iterator[asyncio.Queue[dict[str, object]]]:
    """Capture commands without responding to them."""
    sent: asyncio.Queue[dict[str, object]] = asyncio.Queue()

    @callback
    def send(call: ServiceCall) -> None:
        sent.put_nowait(json.loads(call.data["params"]["data"]))

    hass.services.async_register("zha", "issue_zigbee_cluster_command", send)
    yield sent
    hass.services.async_remove("zha", "issue_zigbee_cluster_command")


async def test_cancelled_caller_keeps_command_reserved(
    hass: HomeAssistant,
    client: XBeeHumidifierApiClient,
    sent_commands: asyncio.Queue[dict[str, object]],
) -> None:
    """A late reply finishes its command before another same-name command starts."""
    first = asyncio.create_task(client.async_command("bind", "first", retry_count=1))
    assert await sent_commands.get() == {"cmd": "bind", "args": "first"}
    response = client._awaiting["bind"]

    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    assert not response.done()
    assert client._cmd_lock["bind"].locked()

    second = asyncio.create_task(client.async_command("bind", "second", retry_count=1))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert sent_commands.empty()
    assert client._awaiting["bind"] is response

    push = AsyncMock()
    client.add_subscriber("uptime", push)
    await client._async_data_received('{"bind_resp": "first reply", "uptime": 123}')
    assert await sent_commands.get() == {"cmd": "bind", "args": "second"}
    assert response.result() == "first reply"
    await client._async_data_received('{"bind_resp": "second reply"}')
    assert await second == "second reply"
    await hass.async_block_till_done()
    push.assert_awaited_once_with(123)
    assert client._awaiting == {}
    assert client._command_tasks == set()


async def test_cancelled_caller_does_not_cancel_send(
    hass: HomeAssistant, client: XBeeHumidifierApiClient
) -> None:
    """Cancellation during the ZHA service call leaves sending and reply handling alive."""
    sending = asyncio.Event()
    finish_sending = asyncio.Event()
    sent = asyncio.Event()

    async def send(call: ServiceCall) -> None:
        sending.set()
        await finish_sending.wait()
        sent.set()

    hass.services.async_register("zha", "issue_zigbee_cluster_command", send)
    caller = asyncio.create_task(client.async_command("bind", retry_count=1))
    await sending.wait()
    (worker,) = client._command_tasks
    response = client._awaiting["bind"]

    caller.cancel()
    with pytest.raises(asyncio.CancelledError):
        await caller
    assert not response.done()
    assert not worker.done()
    assert client._cmd_lock["bind"].locked()

    finish_sending.set()
    await sent.wait()
    await client._async_data_received('{"bind_resp": "OK"}')
    assert await worker == "OK"
    assert client._awaiting == {}
    assert client._command_tasks == set()
    hass.services.async_remove("zha", "issue_zigbee_cluster_command")


async def test_cancelled_queued_caller_still_executes(
    client: XBeeHumidifierApiClient,
    sent_commands: asyncio.Queue[dict[str, object]],
) -> None:
    """The shield also retains commands waiting for their per-command lock."""
    first = asyncio.create_task(client.async_command("bind", "first", retry_count=1))
    assert await sent_commands.get() == {"cmd": "bind", "args": "first"}
    first_response = client._awaiting["bind"]
    (first_worker,) = client._command_tasks

    queued = asyncio.create_task(client.async_command("bind", "queued", retry_count=1))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    (queued_worker,) = client._command_tasks - {first_worker}
    queued.cancel()
    with pytest.raises(asyncio.CancelledError):
        await queued
    assert not queued_worker.done()
    assert client._awaiting["bind"] is first_response
    assert sent_commands.empty()

    await client._async_data_received('{"bind_resp": "first reply"}')
    assert await first == "first reply"
    assert await sent_commands.get() == {"cmd": "bind", "args": "queued"}
    await client._async_data_received('{"bind_resp": "queued reply"}')
    assert await queued_worker == "queued reply"
    assert client._awaiting == {}
    assert client._command_tasks == set()


async def test_timeout_and_retries_survive_caller_cancellation(
    client: XBeeHumidifierApiClient,
    sent_commands: asyncio.Queue[dict[str, object]],
) -> None:
    """The original timeout expires each attempt and releases the command for reuse."""
    with patch(
        "custom_components.xbee_humidifier.coordinator.REMOTE_COMMAND_TIMEOUT", 0.1
    ):
        caller = asyncio.create_task(client.async_command("bind", retry_count=2))
        assert await sent_commands.get() == {"cmd": "bind"}
        (worker,) = client._command_tasks
        first_response = client._awaiting["bind"]
        caller.cancel()
        with pytest.raises(asyncio.CancelledError):
            await caller
        assert not first_response.done()

        assert await sent_commands.get() == {"cmd": "bind"}
        assert first_response.cancelled()
        assert client._awaiting["bind"] is not first_response
        with pytest.raises(TimeoutError, match="No response to bind command"):
            await worker
        assert client._awaiting == {}
        assert client._command_tasks == set()
        assert not client._cmd_lock["bind"].locked()
        assert sent_commands.empty()

        recovered = asyncio.create_task(client.async_command("bind", retry_count=1))
        assert await sent_commands.get() == {"cmd": "bind"}
        await client._async_data_received('{"bind_resp": "OK"}')
        assert await recovered == "OK"


async def test_timeout_survives_cancellation_during_send(
    hass: HomeAssistant, client: XBeeHumidifierApiClient
) -> None:
    """The internal timeout still cancels an unresponsive ZHA service call."""
    sending = asyncio.Event()
    sending_cancelled = asyncio.Event()

    async def send(call: ServiceCall) -> None:
        sending.set()
        try:
            await asyncio.Event().wait()
        finally:
            sending_cancelled.set()

    hass.services.async_register("zha", "issue_zigbee_cluster_command", send)
    with patch(
        "custom_components.xbee_humidifier.coordinator.REMOTE_COMMAND_TIMEOUT", 0.1
    ):
        caller = asyncio.create_task(client.async_command("bind", retry_count=1))
        await sending.wait()
        (worker,) = client._command_tasks
        caller.cancel()
        with pytest.raises(asyncio.CancelledError):
            await caller
        assert not sending_cancelled.is_set()
        with pytest.raises(TimeoutError, match="No response to bind command"):
            await worker

    assert sending_cancelled.is_set()
    assert client._awaiting == {}
    assert client._command_tasks == set()
    assert not client._cmd_lock["bind"].locked()
    hass.services.async_remove("zha", "issue_zigbee_cluster_command")


async def test_detached_worker_exception_is_retrieved(
    hass: HomeAssistant, client: XBeeHumidifierApiClient
) -> None:
    """A failed worker is released without an unhandled task exception after cancellation."""
    sending = asyncio.Event()
    fail_sending = asyncio.Event()
    finished = asyncio.Event()

    async def send(call: ServiceCall) -> None:
        sending.set()
        await fail_sending.wait()
        raise RuntimeError("ZHA send failed")

    hass.services.async_register("zha", "issue_zigbee_cluster_command", send)
    with patch.object(hass.loop, "call_exception_handler") as exception_handler:
        caller = asyncio.create_task(client.async_command("bind", retry_count=1))
        await sending.wait()
        (worker,) = client._command_tasks
        worker.add_done_callback(lambda task: finished.set())
        worker_ref = weakref.ref(worker)
        del worker
        caller.cancel()
        with pytest.raises(asyncio.CancelledError):
            await caller
        del caller

        fail_sending.set()
        await finished.wait()
        assert client._command_tasks == set()
        assert client._awaiting == {}
        gc.collect()
        assert worker_ref() is None
        exception_handler.assert_not_called()

    hass.services.async_remove("zha", "issue_zigbee_cluster_command")


async def test_stop_cancels_active_and_queued_commands(
    client: XBeeHumidifierApiClient,
    sent_commands: asyncio.Queue[dict[str, object]],
) -> None:
    """Unloading the client ends its workers without sending queued commands or retries."""
    active = asyncio.create_task(client.async_command("bind", "active", retry_count=2))
    assert await sent_commands.get() == {"cmd": "bind", "args": "active"}
    response = client._awaiting["bind"]
    queued = asyncio.create_task(client.async_command("bind", "queued", retry_count=2))
    await asyncio.sleep(0)
    await asyncio.sleep(0)
    assert len(client._command_tasks) == 2

    client.stop()
    with pytest.raises(asyncio.CancelledError):
        await active
    with pytest.raises(asyncio.CancelledError):
        await queued

    assert response.cancelled()
    assert client._awaiting == {}
    assert client._command_tasks == set()
    assert not client._cmd_lock["bind"].locked()
    assert client._remove_listener is None
    assert sent_commands.empty()


@pytest.mark.parametrize(
    "reply",
    [
        pytest.param("OK", id="success"),
        pytest.param({"err": "Device error"}, id="error"),
    ],
)
async def test_reply_during_stop_preserves_push_updates(
    hass: HomeAssistant,
    client: XBeeHumidifierApiClient,
    sent_commands: asyncio.Queue[dict[str, object]],
    reply: str | dict[str, str],
) -> None:
    """A response queued during unloading cannot complete a cancelled command future."""
    caller = asyncio.create_task(client.async_command("bind", retry_count=1))
    assert await sent_commands.get() == {"cmd": "bind"}
    response = client._awaiting["bind"]
    push = AsyncMock()
    client.add_subscriber("uptime", push)

    client.stop()
    assert response.cancelled()
    await client._async_data_received(json.dumps({"bind_resp": reply, "uptime": 123}))
    with pytest.raises(asyncio.CancelledError):
        await caller
    await hass.async_block_till_done()

    push.assert_awaited_once_with(123)
    assert client._awaiting == {}
    assert client._command_tasks == set()


async def test_stop_consumes_error_reply_received_during_send(
    hass: HomeAssistant, client: XBeeHumidifierApiClient
) -> None:
    """Stopping during send must retrieve a device error that arrived before the await."""
    sending = asyncio.Event()

    async def send(call: ServiceCall) -> None:
        sending.set()
        await asyncio.Event().wait()

    hass.services.async_register("zha", "issue_zigbee_cluster_command", send)
    with patch.object(hass.loop, "call_exception_handler") as exception_handler:
        caller = asyncio.create_task(client.async_command("bind", retry_count=1))
        await sending.wait()
        response_ref = weakref.ref(client._awaiting["bind"])
        await client._async_data_received('{"bind_resp": {"err": "Device error"}}')

        client.stop()
        with pytest.raises(asyncio.CancelledError):
            await caller
        del caller
        await hass.async_block_till_done()
        assert client._command_tasks == set()
        assert client._awaiting == {}
        gc.collect()
        assert response_ref() is None
        exception_handler.assert_not_called()

    hass.services.async_remove("zha", "issue_zigbee_cluster_command")
