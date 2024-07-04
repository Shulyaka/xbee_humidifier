"""Test xbee_humidifier config flow."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow

from custom_components.xbee_humidifier import (
    CONF_AWAY_HUMIDITY,
    CONF_SENSOR,
    CONF_TARGET_HUMIDITY,
)
from custom_components.xbee_humidifier.const import DOMAIN

from .const import MOCK_CONFIG, MOCK_OPTIONS


@pytest.fixture(autouse=True)
def bypass_setup_fixture():
    """Prevent setup."""
    with patch(
        "custom_components.xbee_humidifier.async_setup_entry",
        return_value=True,
    ):
        yield


def test_test(hass):
    """Workaround for https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/discussions/160."""


async def test_successful_config_flow(hass, data_from_device):
    """Test a successful config flow."""
    # Init first step
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # Advance to step 2
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "humidifier_0"

    # Advance to step 3
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_OPTIONS["humidifier_0"]
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "humidifier_1"

    # Advance to step 4
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_OPTIONS["humidifier_1"]
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "humidifier_2"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_OPTIONS["humidifier_2"]
    )

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "00:11:22:33:44:55:66:77"
    assert result["data"] == MOCK_CONFIG
    assert result["options"] == MOCK_OPTIONS
    assert result["result"]


@patch("custom_components.xbee_humidifier.coordinator.XBeeHumidifierApiClient._cmd")
async def test_failed_config_flow(cmd_mock, hass):
    """Test a failed config flow due to timeout error."""
    cmd_mock.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MOCK_CONFIG
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {"base": "No response to unique_id command"}


async def test_options_flow(hass, test_config_entry):
    """Test an options flow."""
    # Initialize an options flow
    result = await hass.config_entries.options.async_init(test_config_entry.entry_id)

    # Verify that the first options step is a humidifier_0 form
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "humidifier_0"

    # Enter some new data into the form
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SENSOR: "sensor.test4",
            CONF_TARGET_HUMIDITY: 50,
            CONF_AWAY_HUMIDITY: 40,
        },
    )

    # Verify step humidifier_0 results
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "humidifier_1"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SENSOR: "sensor.test5",
            CONF_TARGET_HUMIDITY: 50,
            CONF_AWAY_HUMIDITY: 40,
        },
    )

    # Verify step humidifier_1 results
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "humidifier_2"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SENSOR: "sensor.test6",
            CONF_TARGET_HUMIDITY: 50,
            CONF_AWAY_HUMIDITY: 40,
        },
    )

    # Verify that the flow finishes
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["title"] == "00:11:22:33:44:55:66:77"

    # Verify that the options were updated
    assert test_config_entry.options == {
        "humidifier_0": {
            CONF_SENSOR: "sensor.test4",
            CONF_TARGET_HUMIDITY: 50,
            CONF_AWAY_HUMIDITY: 40,
        },
        "humidifier_1": {
            CONF_SENSOR: "sensor.test5",
            CONF_TARGET_HUMIDITY: 50,
            CONF_AWAY_HUMIDITY: 40,
        },
        "humidifier_2": {
            CONF_SENSOR: "sensor.test6",
            CONF_TARGET_HUMIDITY: 50,
            CONF_AWAY_HUMIDITY: 40,
        },
    }
