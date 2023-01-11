"""Test logging lib."""

import sys

sys.path.append("tests/modules")
from xbee import transmit as mock_transmit  # noqa: E402

import flash.lib.logging  # noqa: E402


def test_logging():
    """Test logging."""

    assert flash.lib.logging.getLogger("test.module") == flash.lib.logging.getLogger(
        "test.module"
    )

    logger = flash.lib.logging.getLogger("__main__")

    logger.debug("Test debug message, %s", 123)
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "__main__: DEBUG: Test debug message, 123\n",
    )

    mock_transmit.reset_mock()
    logger.info("Test info message, %s", "123")
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "__main__: INFO: Test info message, 123\n",
    )

    mock_transmit.reset_mock()
    logger.warning("Test warning message, %s", (123,))
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "__main__: WARNING: Test warning message, (123,)\n",
    )

    mock_transmit.reset_mock()
    logger.error("Test error message, %s", {1: 23})
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "__main__: ERROR: Test error message, {1: 23}\n",
    )

    mock_transmit.reset_mock()
    logger.critical("Test critical message, %s, %s", True, False)
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "__main__: CRITICAL: Test critical message, True, False\n",
    )

    mock_transmit.reset_mock()
    logger.set_target(b"\x01\x23\x45\x67\x89\xab\xcd\xef")
    logger.debug("Test debug message, %s", [1, 2, 3])
    mock_transmit.assert_called_once_with(
        b"\x01\x23\x45\x67\x89\xab\xcd\xef",
        "__main__: DEBUG: Test debug message, [1, 2, 3]\n",
    )

    mock_transmit.reset_mock()
    logger2 = flash.lib.logging.getLogger("tests")
    logger2.debug("Test debug message")
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "tests: DEBUG: Test debug message\n",
    )

    mock_transmit.reset_mock()
    logger.set_level(flash.lib.logging.INFO)
    logger.debug("Test debug message")
    assert mock_transmit.call_count == 0

    logger2.debug("Test debug message")
    mock_transmit.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x00\x00\x00",
        "tests: DEBUG: Test debug message\n",
    )

    mock_transmit.reset_mock()
