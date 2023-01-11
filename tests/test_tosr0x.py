"""Test tosr0x lib."""

import sys
from unittest.mock import patch

import pytest

sys.path.append("tests/modules")
sys.modules["time"] = __import__("mock_time")

from time import sleep as mock_sleep, ticks_ms as mock_ticks_ms  # noqa: E402

import flash.lib.tosr0x  # noqa: E402


@patch("flash.lib.tosr0x.stdout.buffer.write")
@patch("flash.lib.tosr0x.stdin.buffer.read")
def test_tosr0x(mock_stdin, mock_stdout):
    """Test Tosr0x class."""
    mock_ticks_ms.return_value = 0
    tosr = flash.lib.tosr0x.Tosr0x()
    mock_stdout.assert_called_once_with("n")

    assert not tosr.switch0
    assert not tosr.switch1
    assert not tosr.switch2
    assert not tosr.switch3
    assert not tosr.switch4

    mock_stdout.reset_mock()
    mock_stdin.return_value = b"\x01"
    tosr.switch1 = True
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "e"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x02"
    tosr.switch2 = True
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "f"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x04"
    tosr.switch3 = True
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "g"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x08"
    tosr.switch4 = True
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "h"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x0f"
    tosr.switch0 = True
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "d"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.switch0 = False
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "n"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.switch1 = False
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "o"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.switch2 = False
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "p"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.switch3 = False
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "q"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    tosr.switch4 = False
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 2
    assert mock_stdout.call_args_list[0].args == "r"
    assert mock_stdout.call_args_list[1].args == "["
    assert mock_sleep.call_count == 0

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x00"
    with pytest.raises(RuntimeError) as excinfo:
        tosr.switch1 = True
    assert str(excinfo.value) == "Failed to update relay state"
    assert mock_stdin.call_count == 20
    assert mock_stdout.call_count == 20
    assert mock_stdout.call_args_list[0].args == "e"
    assert mock_stdout.call_args_list[1].args == "["
    mock_sleep.call_count == 10

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x0f"
    mock_ticks_ms.reset_mock()
    mock_ticks_ms.return_value = 1000
    tosr.update()
    assert tosr.switch0
    assert tosr.switch1
    assert tosr.switch2
    assert tosr.switch3
    assert tosr.switch4
    mock_ticks_ms.return_value = 1100
    tosr.update()
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 1
    assert mock_stdout.call_args_list[0].args == "["
    mock_ticks_ms.return_value = 1300
    tosr.update()
    assert mock_stdin.call_count == 4
    assert mock_stdout.call_count == 2

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\x01\x23"
    assert tosr.temperature == 18.1875
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 1
    assert mock_stdout.call_args_list[0].args == "a"

    mock_stdout.reset_mock()
    mock_stdin.reset_mock()
    mock_stdin.return_value = b"\xff\xb0"
    assert tosr.temperature == -5
    assert mock_stdin.call_count == 2
    assert mock_stdout.call_count == 1
    assert mock_stdout.call_args_list[0].args == "a"
