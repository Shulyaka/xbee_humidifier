"""Constants for xbee_humidifier tests."""

from custom_components.xbee_humidifier import (
    CONF_AWAY_HUMIDITY,
    CONF_DEVICE_IEEE,
    CONF_MAX_HUMIDITY,
    CONF_MIN_HUMIDITY,
    CONF_SENSOR,
    CONF_TARGET_HUMIDITY,
)

IEEE = "00:11:22:33:44:55:66:77"

# Mock config data to be used across multiple tests
MOCK_CONFIG = {
    CONF_DEVICE_IEEE: IEEE,
}

MOCK_OPTIONS = {
    "humidifier_0": {
        CONF_TARGET_HUMIDITY: 42,
        CONF_AWAY_HUMIDITY: 32,
        CONF_MIN_HUMIDITY: 15,
        CONF_MAX_HUMIDITY: 80,
    },
    "humidifier_1": {
        CONF_SENSOR: "sensor.test2",
        CONF_TARGET_HUMIDITY: 42,
        CONF_AWAY_HUMIDITY: 32,
        CONF_MIN_HUMIDITY: 15,
        CONF_MAX_HUMIDITY: 80,
    },
    "humidifier_2": {
        CONF_SENSOR: "sensor.test3",
        CONF_TARGET_HUMIDITY: 42,
        CONF_MIN_HUMIDITY: 15,
        CONF_MAX_HUMIDITY: 80,
    },
}
