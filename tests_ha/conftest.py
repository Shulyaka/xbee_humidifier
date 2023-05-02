"""Global fixtures for xbee_humidifier integration."""


import json
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

try:
    from homeassistant.core import callback
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.xbee_humidifier.const import DOMAIN

    from .const import MOCK_CONFIG
except ImportError:
    pass

pytest_plugins = "pytest_homeassistant_custom_component"


# This fixture enables loading custom integrations in all tests.
# Remove to enable selective use of this fixture
@pytest_asyncio.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
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
    "atcmd": MagicMock(
        return_value="XBee3-PRO Zigbee 3.0 TH RELE: 1010\rBuild: Aug  2 2022 14:33:22\rHV: 4247\rBootloader: 1B2 Compiler: 8030001\rStack: 6760\rOK\x00"
    ),
}


# This fixture enables two-way communication with the device. The calls are logged in the calls
# array. The command responses can be configured with command dict.
@pytest.fixture(name="data_from_device")
def data_from_device_fixture(hass):
    """Configure fake two-way communication."""

    hum_resp = {
        "extra_state_attr": {"sav_hum": 35},
        "is_on": False,
        "cur_hum": None,
        "cap_attr": {"min_hum": 15, "max_hum": 80},
        "available": False,
        "working": False,
        "number": 1,
        "state_attr": {"mode": "normal", "hum": 50},
    }
    commands["hum"].return_value = hum_resp

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

    for x in commands.values():
        x.reset_mock()

    commands["hum"].return_value = hum_resp
    calls.clear()


@pytest_asyncio.fixture
async def test_config_entry(hass):
    """Load and unload hass config entry."""

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")

    await config_entry.async_setup(hass)
    await hass.async_block_till_done()

    yield config_entry

    assert await config_entry.async_unload(hass)
    await hass.async_block_till_done()
