"""Test tosr0x lib."""

from time import sleep_ms
from unittest.mock import patch

import pytest

from flash import tosr0x


@patch("flash.tosr0x.stdout.buffer.write")
@patch("flash.tosr0x.stdin.buffer.read")
def test_tosr0x(mock_stdin, mock_stdout):
    """Test Tosr0x class."""
    tosr = tosr0x.Tosr0x()
    mock_stdout.assert_called_once_with("n")
    mock_stdin.assert_called_once_with()

    assert not tosr.get_relay_state(0)
    assert not tosr.get_relay_state(1)
    assert not tosr.get_relay_state(2)
    assert not tosr.get_relay_state(3)
    assert not tosr.get_relay_state(4)

    mock_stdin.reset_mock()
    mock_stdout.reset_mock()
    mock_stdin.return_value = b"\x01"
    tosr.set_relay_state(1, True)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "e"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x02"
    tosr.set_relay_state(2, True)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "f"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x04"
    tosr.set_relay_state(3, True)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "g"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x08"
    tosr.set_relay_state(4, True)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "h"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x0f"
    tosr.set_relay_state(0, True)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "d"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.set_relay_state(0, False)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "n"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.set_relay_state(1, False)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "o"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.set_relay_state(2, False)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "p"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.set_relay_state(3, False)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "q"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.set_relay_state(4, False)
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "r"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    with pytest.raises(RuntimeError) as excinfo:
        tosr.set_relay_state(1, True)
    assert str(excinfo.value) == "Failed to update relay state"
    assert mock_stdin.call_count == 20
    assert mock_stdout.call_count == 20
    assert mock_stdout.call_args_list[0][0][0] == "e"
    assert mock_stdout.call_args_list[1][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x0f"
    sleep_ms(1000)
    tosr.update()
    assert tosr.get_relay_state(0)
    assert tosr.get_relay_state(1)
    assert tosr.get_relay_state(2)
    assert tosr.get_relay_state(3)
    assert tosr.get_relay_state(4)
    sleep_ms(100)
    tosr.update()
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 1
    assert mock_stdout.call_args_list[0][0][0] == "["
    sleep_ms(200)
    tosr.update()
    assert mock_stdin.call_count == 4
    assert mock_stdout.call_count == 2

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x01\x02"
    sleep_ms(300)
    with pytest.raises(RuntimeError) as excinfo:
        tosr.update()
    assert str(excinfo.value) == "Failed to get relay state: b'\\x01\\x02'"
    assert mock_stdin.call_count == 20
    assert mock_stdout.call_count == 10
    for x in range(10):
        assert mock_stdout.call_args_list[x][0][0] == "["

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x01\x23"
    assert tosr.temperature == 18.1875
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 1
    assert mock_stdout.call_args_list[0][0][0] == "a"

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\xff\xb0"
    assert tosr.temperature == -5
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 1
    assert mock_stdout.call_args_list[0][0][0] == "a"

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x01\x02\x03"
    with pytest.raises(RuntimeError) as excinfo:
        tosr.temperature
    assert str(excinfo.value) == "Failed to get temperature: b'\\x01\\x02\\x03'"
    assert mock_stdin.call_count == 20
    assert mock_stdout.call_count == 10
    for x in range(10):
        assert mock_stdout.call_args_list[x][0][0] == "a"


@patch("flash.tosr0x.stdout.buffer.write")
@patch("flash.tosr0x.stdin.buffer.read")
def test_tosr0x_version(mock_stdin, mock_stdout):
    """Test Tosr0x version."""
    sleep_ms.reset_mock()
    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x0f\x12"
    assert tosr0x.tosr0x_version() == 0x12
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "n"
    assert mock_stdout.call_args_list[1][0][0] == "Z"
    assert mock_stdin.call_count == 3
    assert sleep_ms.call_count == 1

    sleep_ms.reset_mock()
    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x0f"
    assert tosr0x.tosr0x_version() == 0x0F
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0][0][0] == "n"
    assert mock_stdout.call_args_list[1][0][0] == "Z"
    assert mock_stdin.call_count == 4
    assert sleep_ms.call_count == 1

    sleep_ms.reset_mock()
    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    assert tosr0x.tosr0x_version() is None
    assert mock_stdout.call_count == 11
    assert mock_stdout.call_args_list[0][0][0] == "n"
    for x in range(1, 11):
        assert mock_stdout.call_args_list[x][0][0] == "Z"
    assert mock_stdin.call_count == 31
    assert sleep_ms.call_count == 11
