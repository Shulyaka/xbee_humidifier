"""Test xbee_humidifier."""
import json
from unittest.mock import MagicMock

from homeassistant.components.humidifier import (
    DOMAIN as HUMIDIFIER,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import callback
from homeassistant.setup import async_setup_component

ENT_SENSOR = "sensor.test"


def _setup_sensor(hass, humidity):
    """Set up the test sensor."""
    hass.states.async_set(ENT_SENSOR, humidity)


async def test_humidifier_services(hass):
    """Test humidifier services."""
    # Create a mock entry so we don't have to go through config flow

    _setup_sensor(hass, 50)

    calls = []
    commands = {}

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
        response = json.dumps({cmd + "_resp": response})
        hass.bus.async_fire(
            "zha_event",
            {
                "device_ieee": call.data["ieee"],
                "unique_id": call.data["ieee"] + ":232:0x0008",
                "device_id": "abcdef01234567899876543210fedcba",
                "endpoint_id": 232,
                "cluster_id": 8,
                "command": "receive_data",
                "args": {"data": response},
            },
        )

    hass.services.async_register("zha", "issue_zigbee_cluster_command", log_call)

    hum_resp = {
        "extra_state_attr": {"sav_hum": 35},
        "is_on": False,
        "cur_hum": None,
        "cap_attr": {"min_hum": 15, "max_hum": 100},
        "available": False,
        "working": False,
        "number": 1,
        "state_attr": {"mode": "normal", "hum": 50},
    }
    commands["hum"] = MagicMock(return_value=hum_resp)

    assert await async_setup_component(
        hass,
        "humidifier",
        {
            "humidifier": {
                "platform": "xbee_humidifier",
                "name": "test_humidifier_1",
                "target_sensor": ENT_SENSOR,
                "target_humidity": 42,
                "away_humidity": 32,
                "number": 1,
                "device_ieee": "00:11:22:33:44:55:66:77",
            }
        },
    )

    await hass.async_block_till_done()

    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_TURN_OFF,
        service_data={ATTR_ENTITY_ID: "humidifier.test_humidifier_1"},
        blocking=True,
    )

    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_TURN_ON,
        service_data={ATTR_ENTITY_ID: "humidifier.test_humidifier_1"},
        blocking=True,
    )
