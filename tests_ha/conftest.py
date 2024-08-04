"""Global fixtures for xbee_humidifier integration."""

import json
from functools import partial
from unittest.mock import DEFAULT, MagicMock, patch

import pytest

try:
    from homeassistant.core import callback
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.xbee_humidifier.const import DOMAIN

    from .const import MOCK_CONFIG, MOCK_OPTIONS
except ImportError:
    # Do not import unwanted stuff for micropython tests.
    # Due to pytest bug it stills tries to import this file
    # even for the tests from a separate directory.
    pass

pytest_plugins = "pytest_homeassistant_custom_component.plugins"


# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss
# persistent notifications. These calls would fail without this fixture since the
# persistent_notification integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This is used to access calls and configure command responses
calls = []
cached_values = {}


_NO_ARGS = "no args"


def _cmd_handler(cmd, args=_NO_ARGS):
    number = None
    if isinstance(args, list):
        if args and isinstance(args[0], int):
            number = args[0]
            args = args[1:]
        if len(args) == 1:
            args = args[0]
        elif not args:
            args = _NO_ARGS
    elif isinstance(args, dict):
        if "number" in args:
            number = args.pop("number")
        if len(args) == 1:
            args = args.values()[0]
        elif not args:
            args = _NO_ARGS
    elif isinstance(args, int) and cmd in (
        "sav_hum",
        "available",
        "hum",
        "target_hum",
        "mode",
        "cur_hum",
        "valve",
        "zone",
    ):
        number = args
        args = _NO_ARGS

    if args == _NO_ARGS:
        value = cached_values.get(cmd)
        if number is not None and value:
            value = value.get(number)
        if value is not None:
            return value
        return DEFAULT

    if number is not None:
        cached_values.setdefault(cmd, {})[number] = args
    else:
        cached_values[cmd] = args
    return "OK"


def _uptime_handler(args=None):
    if args is None:
        return DEFAULT
    commands["uptime"].return_value = args
    return "OK"


commands = {
    "sav_hum": MagicMock(side_effect=partial(_cmd_handler, "sav_hum")),
    "available": MagicMock(),
    "hum": MagicMock(side_effect=partial(_cmd_handler, "hum")),
    "target_hum": MagicMock(side_effect=partial(_cmd_handler, "target_hum")),
    "mode": MagicMock(side_effect=partial(_cmd_handler, "mode")),
    "cur_hum": MagicMock(side_effect=partial(_cmd_handler, "cur_hum")),
    "atcmd": MagicMock(),
    "pump_temp": MagicMock(),
    "pressure_in": MagicMock(),
    "valve": MagicMock(side_effect=partial(_cmd_handler, "valve")),
    "pump": MagicMock(side_effect=partial(_cmd_handler, "pump")),
    "pump_block": MagicMock(side_effect=partial(_cmd_handler, "pump_block")),
    "fan": MagicMock(side_effect=partial(_cmd_handler, "fan")),
    "aux_led": MagicMock(side_effect=partial(_cmd_handler, "aux_led")),
    "pump_speed": MagicMock(side_effect=partial(_cmd_handler, "pump_speed")),
    "uptime": MagicMock(side_effect=_uptime_handler),
    "reset_cause": MagicMock(),
    "zone": MagicMock(side_effect=partial(_cmd_handler, "zone")),
}


# This fixture enables two-way communication with the device. The calls are logged
# in the calls array. The command responses can be configured with command dict.
@pytest.fixture(name="data_from_device")
def data_from_device_fixture(hass):
    """Configure fake two-way communication."""
    for x in commands.values():
        x.reset_mock()

    cached_values.clear()

    commands["atcmd"].return_value = (
        "XBee3-PRO Zigbee 3.0 TH RELE: 1010\rBuild: Aug  2 2022 14:33:22\r"
        "HV: 4247\rBootloader: 1B2 Compiler: 8030001\rStack: 6760\rOK\x00"
    )
    commands["sav_hum"].return_value = 35
    commands["available"].return_value = False
    commands["hum"].return_value = False
    commands["target_hum"].return_value = 50
    commands["mode"].return_value = "normal"
    commands["cur_hum"].return_value = None
    commands["pump_temp"].return_value = 31
    commands["pressure_in"].return_value = 3879
    commands["valve"].return_value = False
    commands["pump"].return_value = False
    commands["pump_block"].return_value = False
    commands["fan"].return_value = False
    commands["aux_led"].return_value = False
    commands["pump_speed"].return_value = 252
    commands["uptime"].return_value = -10
    commands["uptime"].side_effect = _uptime_handler
    commands["reset_cause"].return_value = 6
    commands["zone"].return_value = False

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
    def log_call(call):
        """Log service calls."""
        calls.append(call)
        data = json.loads(call.data["params"]["data"])
        cmd = data["cmd"]
        if cmd not in commands:
            commands[cmd] = MagicMock(return_value="OK")
        if "args" in data:
            response = commands[cmd](data["args"])
        else:
            response = commands[cmd]()
        data_from_device(hass, call.data["ieee"], {cmd + "_resp": response})

    hass.services.async_register("zha", "issue_zigbee_cluster_command", log_call)

    calls.clear()

    yield data_from_device

    hass.services.async_remove("zha", "issue_zigbee_cluster_command")


# This fixture loads and unloads the test config entry
@pytest.fixture
async def test_config_entry(hass):
    """Load and unload hass config entry."""

    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CONFIG, options=MOCK_OPTIONS, entry_id="test"
    )

    await hass.config_entries.async_add(config_entry)
    await hass.async_block_till_done()

    yield config_entry

    await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()
