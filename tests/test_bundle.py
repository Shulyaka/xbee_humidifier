"""Test bundle."""

import importlib
from unittest.mock import call

import bundle
from machine import soft_reset as mock_soft_reset
from micropython import opt_level as mock_opt_level
from uos import (
    bundle as mock_bundle,
    compile as mock_compile,
    listdir as mock_listdir,
    remove as mock_remove,
    sync as mock_sync,
)
from xbee import atcmd as mock_atcmd


def test_bundle_compile():
    """Test compile."""
    assert "bundle.mpy" not in bundle._bundle_list
    assert "main.mpy" not in bundle._bundle_list
    assert all(x[-4:] == ".mpy" for x in bundle._bundle_list)

    mock_listdir.return_value = ["test.py"]
    mock_compile.reset_mock()
    mock_opt_level.reset_mock()
    mock_atcmd.reset_mock()
    mock_remove.reset_mock()
    mock_sync.reset_mock()
    mock_bundle.reset_mock()

    def remove(name):
        if name == "test.mpy":
            raise OSError("No such file or directory")

    mock_remove.side_effect = remove

    importlib.reload(bundle)

    mock_opt_level.assert_called_once_with(3)
    mock_atcmd.assert_called_once_with("AP", 0)
    assert mock_compile.call_args_list == [call("test.py"), call("test.py")]
    assert mock_remove.call_args_list == [
        call("test.mpy"),
        call("test.py"),
        call("test.mpy"),
        call("test.py"),
        call("bundle.mpy"),
    ]
    assert mock_sync.call_args_list == [call(), call()]
    assert mock_bundle.call_count == 2
    mock_remove.side_effect = None


def test_bundle_compile_memory_error():
    """Test compile with memory error."""
    mock_listdir.return_value = ["test.py"]
    mock_compile.reset_mock()
    mock_soft_reset.reset_mock()

    mock_compile.side_effect = MemoryError("Not enough memory")

    importlib.reload(bundle)

    mock_compile.side_effect = None
    mock_compile.assert_called_once_with("test.py")
    mock_soft_reset.assert_called_once_with()


def test_bundle_compile_main_bundle():
    """Test that main.py and bundle.py are compiled first."""
    mock_listdir.return_value = ["aaa.py", "bundle.py", "main.py", "zzz.py"]
    mock_compile.reset_mock()
    mock_opt_level.reset_mock()
    mock_atcmd.reset_mock()
    mock_remove.reset_mock()
    mock_sync.reset_mock()
    mock_bundle.reset_mock()

    importlib.reload(bundle)

    mock_opt_level.assert_called_once_with(3)
    mock_atcmd.assert_called_once_with("AP", 0)
    assert mock_compile.call_args_list[:2] == [call("main.py"), call("bundle.py")]
    assert mock_sync.call_count == 2
    assert mock_bundle.call_count == 3


def test_bundle_all_compiled():
    """Test bundle after compile."""
    mock_listdir.return_value = ["bundle.mpy", "test.mpy"]
    mock_atcmd.reset_mock()
    mock_remove.reset_mock()
    mock_sync.reset_mock()
    mock_soft_reset.reset_mock()
    mock_bundle.reset_mock()
    mock_bundle.return_value = ["bundle"]

    importlib.reload(bundle)

    mock_atcmd.assert_called_once_with("AP", 0)
    mock_remove.assert_called_once_with("bundle.mpy")
    mock_sync.assert_called_once_with()
    mock_soft_reset.assert_called_once_with()
    assert mock_bundle.call_count == 3
