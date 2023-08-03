"""Test Makefile."""

import os

import mpy_cross

_mpy_cross_path = os.path.dirname(mpy_cross.mpy_cross)
if _mpy_cross_path not in os.environ["PATH"]:
    os.environ["PATH"] = os.environ["PATH"] + ":" + _mpy_cross_path


def test_compile():
    """Test compilation."""

    assert os.system("make -C flash") == 0


def test_clean():
    """Test clean-up."""

    assert os.system("make -C flash clean") == 0
