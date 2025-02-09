"""DataUpdateCoordinator for xbee_humidifier."""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import logging

from homeassistant.components.zha import DOMAIN as ZHA_DOMAIN
from homeassistant.components.zha.websocket_api import (
    SERVICE_ISSUE_ZIGBEE_CLUSTER_COMMAND,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_COMMAND
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from zha.application.const import (
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

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ATTR_DATA = "data"

XBEE_DATA_CLUSTER = 0x11
SERIAL_DATA_CMD = 0x0000
XBEE_DATA_ENDPOINT = 0xE8

REMOTE_COMMAND_TIMEOUT = 5
DEFAULT_RETRY_COUNT = 5


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
        def ieee_event_filter(event_data):
            return (
                event_data.get("command") == "receive_data"
                and event_data.get("device_ieee") == self.device_ieee
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

    def command(self, command, *args, retry_count=3, **kwargs):
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
            self.async_command(command, *args, **kwargs, retry_count=retry_count),
            self.hass.loop,
        ).result()

    async def async_command(
        self, command, *args, retry_count=DEFAULT_RETRY_COUNT, **kwargs
    ):
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
            e = ValueError("Non-positive retry_count")
            for i in range(retry_count):
                if i:
                    _LOGGER.debug("Retrying...")
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
                    e = TimeoutError(f"No response to {command} command")
                except Exception as exp:
                    _LOGGER.error(
                        f"Error getting response for {command} command: {exp}"
                    )
                    e = exp

            raise e

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
            if key == "nonce":
                continue
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
                    self.hass.async_create_task(listener(value))
            else:
                _LOGGER.warning("No callback for %s", {key: value})

        if "data_received" in self._callbacks:
            for listener in self._callbacks["data_received"]:
                self.hass.async_create_task(listener(data))


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
            update_interval=dt.timedelta(minutes=10),
        )

        self.client = client
        self._xbee_logger = logging.getLogger(DOMAIN)
        self._device_reset = True
        self._callbacks = {}
        self._uptime = None

        async def async_log(data):
            self._xbee_logger.log(data["sev"], data["msg"])

        self._remove_log_handler = self.client.add_subscriber("log", async_log)

        async def device_reset():
            if not self._device_reset:
                self._device_reset = True
                await self.async_refresh()

        self._remove_device_reset_handler = self.add_subscriber(
            "device_reset", device_reset
        )

        async def async_data_received(data):
            if not self.last_update_success:
                await self.device_reconnect()

        self._remove_data_received_handler = self.client.add_subscriber(
            "data_received", async_data_received
        )

        async def device_reconnect():
            await self.async_request_refresh()

        self._remove_device_reconnect_handler = self.add_subscriber(
            "device_reconnect", device_reconnect
        )

        async def update_uptime(value):
            if value <= 0:
                self._uptime = value
                self._timestamp = dt.datetime.now(tz=dt.timezone.utc).timestamp()
                await self.device_reset()

        self._remove_update_uptime_handler = self.client.add_subscriber(
            "uptime", update_uptime
        )

    async def device_reset(self):
        """Run triggers on device reset."""
        for listener in self._callbacks["device_reset"]:
            self.hass.async_create_task(listener())

    async def device_reconnect(self):
        """Run triggers on restore of a broken connection."""
        for listener in self._callbacks["device_reconnect"]:
            self.hass.async_create_task(listener())

    def add_subscriber(self, name, callback):
        """Register listener."""
        if name not in self._callbacks:
            self._callbacks[name] = []
        self._callbacks[name].append(callback)
        return lambda: self._callbacks[name].remove(callback)

    def __del__(self):
        """Destructor."""
        self.stop()

    def stop(self):
        """Unsubscribe events."""
        self.client.stop()
        if self._remove_log_handler is not None:
            self._remove_log_handler()
            self._remove_log_handler = None
        if self._remove_data_received_handler is not None:
            self._remove_data_received_handler()
            self._remove_data_received_handler = None
        if self._remove_device_reset_handler is not None:
            self._remove_device_reset_handler()
            self._remove_device_reset_handler = None
        if self._remove_update_uptime_handler is not None:
            self._remove_update_uptime_handler()
            self._remove_update_uptime_handler = None
        if self._remove_device_reconnect_handler is not None:
            self._remove_device_reconnect_handler()
            self._remove_device_reconnect_handler = None

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
        data = {"humidifier": {}, "valve": {}}
        if self._device_reset and self._uptime is not None:
            data["uptime"] = self._uptime
        else:
            data["uptime"] = await self.client.async_command("uptime")
            self._timestamp = dt.datetime.now(tz=dt.timezone.utc).timestamp()
        self._uptime = None
        data["reset_cause"] = await self.client.async_command("reset_cause")
        data["pump"] = await self.client.async_command("pump")
        data["fan"] = await self.client.async_command("fan")
        data["aux_led"] = await self.client.async_command("aux_led")
        data["pump_temp"] = await self.client.async_command("pump_temp")
        data["pressure_in"] = await self.client.async_command("pressure_in")
        data["pump_speed"] = await self.client.async_command("pump_speed")
        for number in range(0, 4):
            data["valve"][number] = await self.client.async_command("valve", number)
        if data["uptime"] > 0:
            data["pump_block"] = await self.client.async_command("pump_block")
            for number in range(0, 3):
                data["humidifier"][number] = {}
                data["humidifier"][number]["sav_hum"] = await self.client.async_command(
                    "sav_hum", number
                )
                data["humidifier"][number][
                    "available"
                ] = await self.client.async_command("available", number)
                data["humidifier"][number]["working"] = await self.client.async_command(
                    "zone", number
                )
                data["humidifier"][number]["is_on"] = await self.client.async_command(
                    "hum", number
                )
                data["humidifier"][number]["cur_hum"] = await self.client.async_command(
                    "cur_hum", number
                )
                data["humidifier"][number][
                    "target_hum"
                ] = await self.client.async_command("target_hum", number)
                data["humidifier"][number]["mode"] = await self.client.async_command(
                    "mode", number
                )
        else:
            if not self._device_reset:
                self._device_reset = True
                await self.device_reset()
            value = int(self._timestamp + data["uptime"] + 0.5)
            await self.client.async_command("uptime", value)
            data["new_uptime"] = value
            self._device_reset = False

        return data
