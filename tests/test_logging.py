"""Test logging lib."""

from xbee import transmit as mock_transmit

from flash.lib import logging


def test_logging():
    """Test logging."""
    assert logging.getLogger("test.module") == logging.getLogger("test.module")

    logger = logging.getLogger("__main__")

    mock_transmit.reset_mock()
    logger.debug("Test debug message, %s", 123)
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "10: Test debug message, 123\n",
    )

    mock_transmit.reset_mock()
    logger.info("Test info message, %s", "123")
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "20: Test info message, 123\n",
    )

    mock_transmit.reset_mock()
    logger.warning("Test warning message, %s", (123,))
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "30: Test warning message, (123,)\n",
    )

    mock_transmit.reset_mock()
    logger.error("Test error message, %s", {1: 23})
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "40: Test error message, {1: 23}\n",
    )

    mock_transmit.reset_mock()
    logger.critical("Test critical message, %s, %s", True, False)
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "50: Test critical message, True, False\n",
    )

    mock_transmit.reset_mock()
    logger.setTarget(b"\x01\x23\x45\x67\x89\xab\xcd\xef")
    logger.debug("Test debug message, %s", [1, 2, 3])
    mock_transmit.assert_called_once_with(
        b"\x01\x23\x45\x67\x89\xab\xcd\xef",
        "10: Test debug message, [1, 2, 3]\n",
    )

    logger2 = logging.getLogger("tests")
    assert logger2 == logger

    mock_transmit.reset_mock()
    assert logger.getEffectiveLevel() == logging.DEBUG
    logger.setLevel(logging.INFO)
    assert logger.getEffectiveLevel() == logging.INFO
    logger.debug("Test debug message")
    assert mock_transmit.call_count == 0
