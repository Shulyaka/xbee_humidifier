"""DataUpdateCoordinator for xbee_humidifier."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta

from homeassistant.components.zha import DOMAIN as ZHA_DOMAIN
from homeassistant.components.zha.core.const import (
    ATTR_CLUSTER_ID,
    ATTR_CLUSTER_TYPE,
    ATTR_COMMAND_TYPE,
    ATTR_ENDPOINT_ID,
    ATTR_IEEE,
    ATTR_PARAMS,
    CLUSTER_COMMAND_SERVER,
    CLUSTER_TYPE_IN,
    ZHA_EVENT,
)
from homeassistant.components.zha.websocket_api import (
    SERVICE_ISSUE_ZIGBEE_CLUSTER_COMMAND,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_COMMAND
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ATTR_DATA = "data"

XBEE_DATA_CLUSTER = 0x11
SERIAL_DATA_CMD = 0x0000
XBEE_DATA_ENDPOINT = 0xE8

REMOTE_COMMAND_TIMEOUT = 10


class XBeeHumidifierApiClient:
    """Class to fetch data from XBeeHumidifier."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_ieee,
    ) -> None:
        """Initialize the XBee Humidifier API Client."""

        self.hass = hass
        self.device_ieee = device_ieee
        self._cmd_lock = {}
        self._cmd_resp_lock = asyncio.Lock()
        self._awaiting = {}
        self._callbacks = {}
        self._remove_listener = None
        self.start()

    def __del__(self):
        """Destructor."""
        self.stop()

    def start(self):
        """Subscribe events."""
        if self._remove_listener:
            return

        @callback
        async def async_zha_event(event):
            await self._async_data_received(event.data["args"]["data"])

        @callback
        def ieee_event_filter(event):
            return (
                event.data.get("command") == "receive_data"
                and event.data.get("device_ieee") == self.device_ieee
            )

        self._remove_listener = self.hass.bus.async_listen(
            ZHA_EVENT, async_zha_event, ieee_event_filter
        )

    def stop(self):
        """Unsubscribe events."""
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    def add_subscriber(self, name, callback):
        """Register listener."""
        if name not in self._callbacks:
            self._callbacks[name] = []
        self._callbacks[name].append(callback)
        return lambda: self._callbacks[name].remove(callback)

    def command(self, command, *args, **kwargs):
        """Issue xbee humidifier command synchronously."""
        try:
            if self.hass.loop == asyncio.get_running_loop():
                raise NotImplementedError(
                    "The synchronous function cannot be run from the main hass loop, "
                    "run from thread instead or use async version"
                )
        except RuntimeError as e:
            if str(e) == "no running event loop":
                pass
            else:
                raise

        return asyncio.run_coroutine_threadsafe(
            self.async_command(command, *args, **kwargs), self.hass.loop
        ).result()

    async def async_command(self, command, *args, **kwargs):
        """Issue xbee humidifier command asynchronously."""
        if len(args) > 0 and len(kwargs) > 0:
            data = {"cmd": command, "args": (args, kwargs)}
        elif len(args) > 1:
            data = {"cmd": command, "args": args}
        elif len(args) == 1:
            data = {"cmd": command, "args": args[0]}
        elif len(kwargs) > 0:
            data = {"cmd": command, "args": kwargs}
        else:
            data = {"cmd": command}

        data = json.dumps(data)

        _LOGGER.debug("data: %s", data)

        if command not in self._cmd_lock:
            self._cmd_lock[command] = asyncio.Lock()

        async with self._cmd_lock[command]:
            try:
                return await asyncio.wait_for(
                    self._cmd(command, data),
                    timeout=REMOTE_COMMAND_TIMEOUT,
                )
            except TimeoutError:
                _LOGGER.error(f"No response to {command} command")
                try:
                    del self._awaiting[command]
                except KeyError:
                    pass
                raise TimeoutError(f"No response to {command} command")

    async def _cmd(self, command, data):
        if command in self._awaiting:
            raise RuntimeError("Command is already executing")

        data = {
            ATTR_CLUSTER_ID: XBEE_DATA_CLUSTER,
            ATTR_CLUSTER_TYPE: CLUSTER_TYPE_IN,
            ATTR_COMMAND: SERIAL_DATA_CMD,
            ATTR_COMMAND_TYPE: CLUSTER_COMMAND_SERVER,
            ATTR_ENDPOINT_ID: XBEE_DATA_ENDPOINT,
            ATTR_IEEE: self.device_ieee,
            ATTR_PARAMS: {ATTR_DATA: data},
        }

        future = asyncio.Future()

        self._awaiting[command] = future

        try:
            await self.hass.services.async_call(
                ZHA_DOMAIN, SERVICE_ISSUE_ZIGBEE_CLUSTER_COMMAND, data, True
            )
        except Exception as e:
            _LOGGER.error(e)
            future.set_exception(e)
            del self._awaiting[command]

        return await future

    async def _async_data_received(self, data):
        data = json.loads(data)
        for key, value in data.items():
            if key[-5:] == "_resp":
                async with self._cmd_resp_lock:
                    command = key[:-5]
                    if command not in self._awaiting:
                        continue
                    future = self._awaiting.pop(command)
                    if isinstance(value, dict) and "err" in value:
                        future.set_exception(
                            RuntimeError(f"Command response: {value['err']}")
                        )
                        continue
                    _LOGGER.debug("%s response: %s", command, value)
                    future.set_result(value)
            elif key in self._callbacks:
                if key != "log":
                    _LOGGER.debug("%s = %s", key, value)
                for listener in self._callbacks[key]:
                    try:
                        await listener(value)
                    except Exception as e:
                        _LOGGER.error("callback error for %s", listener)
                        _LOGGER.error(type(e).__name__ + ": " + str(e))
            else:
                _LOGGER.warning("No callback for %s", {key: value})

        if "data_received" in self._callbacks:
            for listener in self._callbacks["data_received"]:
                try:
                    await listener(data)
                except Exception as e:
                    _LOGGER.error("callback error for %s", listener)
                    _LOGGER.error(type(e).__name__ + ": " + str(e))


class XBeeHumidifierDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from XBeeHumidifier."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: XBeeHumidifierApiClient,
    ) -> None:
        """Initialize the XBee Humidifier Client."""
        super().__init__(
            hass=hass,
            logger=logging.getLogger(__package__),
            name=DOMAIN,
            update_method=self.async_update_data,
            update_interval=timedelta(minutes=10),
        )

        self.client = client

        self._xbee_logger = logging.getLogger("xbee_humidifier")

        async def async_log(data):
            self._xbee_logger.log(data["sev"], data["msg"])
            if data["msg"] in ("Not initialized", "Main loop started"):
                await self.async_request_refresh()

        self._remove_log_handler = self.client.add_subscriber("log", async_log)

        async def async_data_received(data):
            self.last_update_success = True

        self._remove_data_received_handler = self.client.add_subscriber(
            "data_received", async_data_received
        )

    def __del__(self):
        """Destructor."""
        self.stop()

    def stop(self):
        """Unsubscribe events."""
        self.client.stop()
        if self._remove_log_handler:
            self._remove_log_handler()
            self._remove_log_handler = None
        if self._remove_data_received_handler:
            self._remove_data_received_handler()
            self._remove_data_received_handler = None

    async def async_config_entry_first_refresh(self) -> None:
        """Refresh data for the first time when a config entry is setup."""
        await super().async_config_entry_first_refresh()
        self.unique_id = await self.client.async_command("unique_id")
        version_info = await self.client.async_command("atcmd", "VL")
        version_info = (
            ("Model: " + version_info)
            .replace(" RELE", "\rVR")
            .replace(" Compiler", "\rCompiler")
            .replace("Bootloader", "VH")
            .replace("\rOK\x00", "")
            .split("\r")
        )
        version_info = [v.split(": ", 1) for v in version_info]
        self.version_info = dict(version_info)

    @callback
    async def async_update_data(self):
        """Update data."""
        await self.client.async_command("bind")
        data = {}
        data[0] = await self.client.async_command("hum", 0)
        data[1] = await self.client.async_command("hum", 1)
        data[2] = await self.client.async_command("hum", 2)
        return data
