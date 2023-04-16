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
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xbee_humidifier.const import DOMAIN

from .conftest import calls, commands
from .const import IEEE, MOCK_CONFIG

ENTITY = "humidifier.xbee_humidifier_2_humidifier"
ENT_SENSOR = "sensor.test2"


def _setup_sensor(hass, humidity):
    """Set up the test sensor."""
    hass.states.async_set(ENT_SENSOR, humidity)


async def test_humidifier_services(hass, caplog, data_from_device):
    """Test humidifier services."""

    _setup_sensor(hass, 50)

    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")
    await config_entry.async_setup(hass)
    await hass.async_block_till_done()

    assert commands["hum"].call_args[0][0] == [[1], {"cur_hum": "50"}]

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
    assert state.attributes.get("min_humidity") == 15
    assert state.attributes.get("max_humidity") == 80
    assert state.attributes.get("mode") == "normal"
    assert state.attributes.get("saved_humidity") == 32
    assert state.attributes.get("supported_features") == 1

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

    commands["hum"].reset_mock()
    _setup_sensor(hass, 49)
    await hass.async_block_till_done()

    assert len(calls) == 1
    calls.clear()
    commands["hum"].assert_called_once_with([[1], {"cur_hum": "49"}])

    assert await config_entry.async_unload(hass)
    await hass.async_block_till_done()
