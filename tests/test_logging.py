"""Test logging lib."""

from json import loads as json_loads

from xbee import transmit as mock_transmit

from flash.lib import logging


def test_logging():
    """Test logging."""
    assert logging.getLogger("test.module") == logging.getLogger("test.module")

    logger = logging.getLogger("__main__")

    mock_transmit.reset_mock()
    logger.debug("Test debug message, %s", 123)
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "log": {"sev": 10, "msg": "Test debug message, 123"}
    }

    mock_transmit.reset_mock()
    logger.info("Test info message, %s", "123")
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "log": {"sev": 20, "msg": "Test info message, 123"}
    }

    mock_transmit.reset_mock()
    logger.warning("Test warning message, %s", (123,))
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "log": {"sev": 30, "msg": "Test warning message, (123,)"}
    }

    mock_transmit.reset_mock()
    logger.error("Test error message, %s", {1: 23})
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "log": {"sev": 40, "msg": "Test error message, {1: 23}"}
    }

    mock_transmit.reset_mock()
    logger.critical("Test critical message, %s, %s", True, False)
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x00\x00\x00\x00\x00\x00\x00\x00"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "log": {"sev": 50, "msg": "Test critical message, True, False"}
    }

    mock_transmit.reset_mock()
    logger.setTarget(b"\x01\x23\x45\x67\x89\xab\xcd\xef")
    logger.debug("Test debug message, %s", [1, 2, 3])
    assert mock_transmit.call_count == 1
    assert mock_transmit.call_args[0][0] == b"\x01\x23\x45\x67\x89\xab\xcd\xef"
    assert json_loads(mock_transmit.call_args[0][1]) == {
        "log": {"sev": 10, "msg": "Test debug message, [1, 2, 3]"}
    }

    logger2 = logging.getLogger("tests")
    assert logger2 == logger

    mock_transmit.reset_mock()
    assert logger.getEffectiveLevel() == logging.DEBUG
    logger.setLevel(logging.INFO)
    assert logger.getEffectiveLevel() == logging.INFO
    logger.debug("Test debug message")
    assert mock_transmit.call_count == 0

    mock_transmit.side_effect = OSError("EAGAIN")
    logger.info("This message does not raise exception")
    mock_transmit.side_effect = None
