"""Global fixtures for xbee_humidifier integration."""


import json
from unittest.mock import MagicMock, patch

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

pytest_plugins = "pytest_homeassistant_custom_component"


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
commands = {
    "hum": MagicMock(return_value="OK"),
    "target_hum": MagicMock(return_value=50),
    "mode": MagicMock(return_value="normal"),
    "cur_hum": MagicMock(return_value=None),
    "atcmd": MagicMock(
        return_value="XBee3-PRO Zigbee 3.0 TH RELE: 1010\rBuild: Aug  2 2022 14:33:22\r"
        "HV: 4247\rBootloader: 1B2 Compiler: 8030001\rStack: 6760\rOK\x00"
    ),
    "pump_temp": MagicMock(return_value=31),
    "pressure_in": MagicMock(return_value=3879),
    "valve": MagicMock(return_value=False),
    "pump": MagicMock(return_value=False),
    "pump_block": MagicMock(return_value=False),
    "fan": MagicMock(return_value=False),
    "aux_led": MagicMock(return_value=False),
    "pump_speed": MagicMock(return_value=252),
}


# This fixture enables two-way communication with the device. The calls are logged
# in the calls array. The command responses can be configured with command dict.
@pytest.fixture(name="data_from_device")
def data_from_device_fixture(hass):
    """Configure fake two-way communication."""

    hum_resp = {
        "extra_state_attr": {"sav_hum": 35},
        "is_on": False,
        "cap_attr": {"min_hum": 15, "max_hum": 80},
        "available": False,
        "working": False,
    }
    commands["hum"].return_value = hum_resp
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

    yield data_from_device

    hass.services.async_remove("zha", "issue_zigbee_cluster_command")

    for x in commands.values():
        x.reset_mock()

    commands["hum"].return_value = hum_resp
    calls.clear()


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

    await hass.async_block_till_done()
    await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()
