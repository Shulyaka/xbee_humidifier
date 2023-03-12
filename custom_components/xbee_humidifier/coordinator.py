"""DataUpdateCoordinator for xbee_humidifier."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import json
import logging

from homeassistant.components.zha import DOMAIN as ZHA_DOMAIN
from homeassistant.components.zha.api import SERVICE_ISSUE_ZIGBEE_CLUSTER_COMMAND
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

REMOTE_COMMAND_TIMEOUT = 30


class XBeeHumidifierApiClient:
    """Class to fetch data from XBeeHumidifier."""

    def __init__(
        self,
        hass: HomeAssistant,
        device_ieee,
    ) -> None:
        """Inititialize the XBee Humidifier API Client."""

        self.hass = hass
        self._device_ieee = device_ieee
        self._cmd_lock = asyncio.Lock()
        self._cmd_resp_lock = asyncio.Lock()
        self._awaiting = {}
        self._callbacks = {}

        @callback
        async def async_zha_event(event):
            await self._async_data_received(event.data["args"]["data"])

        @callback
        def ieee_event_filter(event):
            return (
                event.data["command"] == "receive_data"
                and event.data["device_ieee"] == self._device_ieee
            )

        self._remove_listener = self.hass.bus.async_listen(
            ZHA_EVENT, async_zha_event, ieee_event_filter
        )

    def __del__(self):
        """Unsubscribe events."""
        self._remove_listener()

    def add_subscriber(self, name, callback):
        """Register listener."""
        if name not in self._callbacks:
            self._callbacks[name] = []
        self._callbacks[name].append(callback)
        return lambda: self._callbacks[name].remove(callback)

    async def command(self, command, *args, **kwargs):
        """Issue xbee humidifier command."""
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

        async with self._cmd_lock:
            try:
                return await asyncio.wait_for(
                    await self._cmd(command, data),
                    timeout=REMOTE_COMMAND_TIMEOUT,
                )
            except asyncio.TimeoutError:
                _LOGGER.error("No response to %s command", command)
                del self._awaiting[command]
                raise TimeoutError("No response to %s command" % command)

    async def _cmd(self, command, data):
        if command in self._awaiting:
            raise RuntimeError("Command is already executing")

        data = {
            ATTR_CLUSTER_ID: XBEE_DATA_CLUSTER,
            ATTR_CLUSTER_TYPE: CLUSTER_TYPE_IN,
            ATTR_COMMAND: SERIAL_DATA_CMD,
            ATTR_COMMAND_TYPE: CLUSTER_COMMAND_SERVER,
            ATTR_ENDPOINT_ID: XBEE_DATA_ENDPOINT,
            ATTR_IEEE: self._device_ieee,
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

        return future

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
                            RuntimeError("Command response: {}".format(value["err"]))
                        )
                        continue
                    _LOGGER.debug("%s response: %s", command, value)
                    future.set_result(value)
            elif key in self._callbacks:
                _LOGGER.debug("%s = %s", key, value)
                for listener in self._callbacks[key]:
                    try:
                        await listener(value)
                    except Exception as e:
                        _LOGGER.error("callback error for %s", listener)
                        _LOGGER.error(type(e).__name__ + ": " + str(e))
            else:
                _LOGGER.warning("No callback for %s", {key: value})


class XBeeHumidifierDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from XBeeHumidifier."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: XBeeHumidifierApiClient,
    ) -> None:
        """Inititialize the XBee Humidifier Client."""
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

    def __del__(self):
        """Destructor."""
        self._remove_log_handler()

    @callback
    async def async_update_data(self):
        """Update data."""
        await self.client.command("bind")
