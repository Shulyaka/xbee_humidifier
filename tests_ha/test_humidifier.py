"""Test xbee_humidifier."""
from homeassistant.components.humidifier import (
    ATTR_HUMIDITY,
    DOMAIN as HUMIDIFIER,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_MODE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, ATTR_MODE

from .conftest import calls, commands
from .const import IEEE

ENTITY1 = "humidifier.xbee_humidifier_1_humidifier"
ENTITY2 = "humidifier.xbee_humidifier_2_humidifier"
ENTITY3 = "humidifier.xbee_humidifier_3_humidifier"
ENT_SENSOR = "sensor.test2"


def test_humidifier_init(hass, data_from_device, test_config_entry):
    """Test that all humidifier entities are created."""

    assert hass.states.get(ENTITY1).state == "unavailable"
    assert hass.states.get(ENTITY2).state == "unavailable"
    assert hass.states.get(ENTITY3).state == "unavailable"


def _setup_sensor(hass, humidity):
    """Set up the test sensor."""
    hass.states.async_set(ENT_SENSOR, humidity)


async def test_humidifier_services(hass, data_from_device, test_config_entry):
    """Test humidifier services."""

    commands["cur_hum"].reset_mock()

    _setup_sensor(hass, 50)
    await hass.async_block_till_done()

    commands["cur_hum"].assert_called_once_with([1, 50.0])

    commands["hum"].reset_mock()
    commands["hum"].return_value = "OK"

    assert hass.states.get(ENTITY2).state == "unavailable"

    data_from_device(hass, IEEE, {"available_1": True})
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY2)
    assert state.state == "off"

    assert state.attributes.get("available_modes") == ["normal", "away"]
    assert state.attributes.get("device_class") == "humidifier"
    assert state.attributes.get("friendly_name") == "XBee Humidifier 2 Humidifier"
    assert state.attributes.get("humidity") == 42
    assert state.attributes.get("current_humidity") == 50
    assert state.attributes.get("min_humidity") == 15
    assert state.attributes.get("max_humidity") == 80
    assert state.attributes.get("mode") == "normal"
    assert state.attributes.get("saved_humidity") == 32
    assert state.attributes.get("supported_features") == 1
    assert state.attributes.get("action") == "off"

    calls.clear()

    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY2},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    calls.clear()
    commands["hum"].assert_called_once_with([1, True])
    assert hass.states.get(ENTITY2).state == "on"
    assert hass.states.get(ENTITY2).attributes["action"] == "idle"

    data_from_device(hass, IEEE, {"working_1": True})
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY2).attributes["action"] == "humidifying"

    commands["hum"].reset_mock()
    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_TURN_OFF,
        service_data={ATTR_ENTITY_ID: ENTITY2},
        blocking=True,
    )

    assert len(calls) == 1
    calls.clear()
    commands["hum"].assert_called_once_with([1, False])

    commands["target_hum"].reset_mock()
    commands["target_hum"].return_value = "OK"
    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_SET_HUMIDITY,
        service_data={ATTR_ENTITY_ID: ENTITY2, ATTR_HUMIDITY: 44},
        blocking=True,
    )

    assert len(calls) == 1
    calls.clear()
    commands["target_hum"].assert_called_once_with([1, 44])
    assert hass.states.get(ENTITY2).attributes["humidity"] == 44

    commands["mode"].reset_mock()
    commands["mode"].return_value = "OK"
    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_SET_MODE,
        service_data={ATTR_ENTITY_ID: ENTITY2, ATTR_MODE: "away"},
        blocking=True,
    )

    assert len(calls) == 1
    calls.clear()
    commands["mode"].assert_called_once_with([1, "away"])
    assert hass.states.get(ENTITY2).attributes["humidity"] == 32
    assert hass.states.get(ENTITY2).attributes["saved_humidity"] == 44
    assert hass.states.get(ENTITY2).attributes["mode"] == "away"
    assert hass.states.get(ENTITY2).attributes["action"] == "off"

    commands["cur_hum"].reset_mock()
    _setup_sensor(hass, 49)
    await hass.async_block_till_done()

    assert len(calls) == 1
    calls.clear()
    commands["cur_hum"].assert_called_once_with([1, 49.0])
    assert hass.states.get(ENTITY2).attributes["current_humidity"] == 49

    assert hass.states.get(ENTITY3).state == "unavailable"

    data_from_device(hass, IEEE, {"available_2": True})
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY3)
    assert state.state == "off"

    assert state.attributes.get("available_modes") is None
    assert state.attributes.get("device_class") == "humidifier"
    assert state.attributes.get("friendly_name") == "XBee Humidifier 3 Humidifier"
    assert state.attributes.get("humidity") == 42
    assert state.attributes.get("current_humidity") is None
    assert state.attributes.get("min_humidity") == 15
    assert state.attributes.get("max_humidity") == 80
    assert state.attributes.get("mode") is None
    assert state.attributes.get("saved_humidity") is None
    assert state.attributes.get("supported_features") == 0
    assert state.attributes.get("action") == "off"
