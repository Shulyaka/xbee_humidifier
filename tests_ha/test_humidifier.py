"""Test humidifier."""

from custom_components.xbee_humidifier.humidifier import XBeeHumidifier


def test_humidifier():
    """Test humidifier."""
    humidifier = XBeeHumidifier(
        "Test humidifier",
        "00:11:22:33:44:55:66:77",
        2,
        "sensor.current_humidity",
        42,
        32,
    )

    assert humidifier.is_on is None
