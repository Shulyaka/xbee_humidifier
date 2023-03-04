"""Constants for xbee_humidifier tests."""
from homeassistant.const import CONF_NAME

from custom_components.xbee_humidifier import (
    CONF_AWAY_HUMIDITY,
    CONF_DEVICE_IEEE,
    CONF_SENSOR,
    CONF_TARGET_HUMIDITY,
)

IEEE = "00:11:22:33:44:55:66:77"

# Mock config data to be used across multiple tests
MOCK_CONFIG = {
    CONF_DEVICE_IEEE: IEEE,
    1: {
        CONF_NAME: "test_humidifier_1",
        CONF_SENSOR: "sensor.test1",
        CONF_TARGET_HUMIDITY: 42,
        CONF_AWAY_HUMIDITY: 32,
    },
    2: {
        CONF_NAME: "test_humidifier_2",
        CONF_SENSOR: "sensor.test2",
        CONF_TARGET_HUMIDITY: 42,
        CONF_AWAY_HUMIDITY: 32,
    },
    3: {
        CONF_NAME: "test_humidifier_3",
        CONF_SENSOR: "sensor.test3",
        CONF_TARGET_HUMIDITY: 42,
        CONF_AWAY_HUMIDITY: 32,
    },
}
