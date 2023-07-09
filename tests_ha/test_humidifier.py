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

ENTITY = "humidifier.xbee_humidifier_2_humidifier"
ENT_SENSOR = "sensor.test2"


def test_humidifier_init(hass, data_from_device, test_config_entry):
    """Test that all humidifier entities are created."""

    assert (
        hass.states.get("humidifier.xbee_humidifier_1_humidifier").state
        == "unavailable"
    )
    assert (
        hass.states.get("humidifier.xbee_humidifier_1_humidifier").state
        == "unavailable"
    )
    assert (
        hass.states.get("humidifier.xbee_humidifier_3_humidifier").state
        == "unavailable"
    )


def _setup_sensor(hass, humidity):
    """Set up the test sensor."""
    hass.states.async_set(ENT_SENSOR, humidity)


async def test_humidifier_services(hass, data_from_device, test_config_entry):
    """Test humidifier services."""

    commands["hum"].reset_mock()

    _setup_sensor(hass, 50)
    await hass.async_block_till_done()

    commands["hum"].assert_called_once_with([[1], {"cur_hum": "50"}])

    commands["hum"].reset_mock()
    commands["hum"].return_value = "OK"

    assert hass.states.get(ENTITY).state == "unavailable"

    data_from_device(hass, IEEE, {"available_1": True})
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY)
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
        {ATTR_ENTITY_ID: ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    calls.clear()
    commands["hum"].assert_called_once_with([[1], {"is_on": True}])
    assert hass.states.get(ENTITY).state == "on"
    assert hass.states.get(ENTITY).attributes["action"] == "idle"

    commands["hum"].reset_mock()
    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_TURN_OFF,
        service_data={ATTR_ENTITY_ID: ENTITY},
        blocking=True,
    )

    assert len(calls) == 1
    calls.clear()
    commands["hum"].assert_called_once_with([[1], {"is_on": False}])

    commands["hum"].reset_mock()
    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_SET_HUMIDITY,
        service_data={ATTR_ENTITY_ID: ENTITY, ATTR_HUMIDITY: 44},
        blocking=True,
    )

    assert len(calls) == 1
    calls.clear()
    commands["hum"].assert_called_once_with([[1], {"hum": 44}])
    assert hass.states.get(ENTITY).attributes["humidity"] == 44

    commands["hum"].reset_mock()
    await hass.services.async_call(
        HUMIDIFIER,
        SERVICE_SET_MODE,
        service_data={ATTR_ENTITY_ID: ENTITY, ATTR_MODE: "away"},
        blocking=True,
    )

    assert len(calls) == 1
    calls.clear()
    commands["hum"].assert_called_once_with([[1], {"mode": "away"}])
    assert hass.states.get(ENTITY).attributes["humidity"] == 32
    assert hass.states.get(ENTITY).attributes["saved_humidity"] == 44
    assert hass.states.get(ENTITY).attributes["mode"] == "away"
    assert hass.states.get(ENTITY).attributes["action"] == "humidifying"

    commands["hum"].reset_mock()
    _setup_sensor(hass, 49)
    await hass.async_block_till_done()

    assert len(calls) == 1
    calls.clear()
    commands["hum"].assert_called_once_with([[1], {"cur_hum": "49"}])
    assert hass.states.get(ENTITY).attributes["current_humidity"] == 49
    assert hass.states.get(ENTITY).attributes["action"] == "idle"
