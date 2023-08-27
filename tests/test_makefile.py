"""Test Makefile."""

import os
import tempfile

import mpy_cross

_mpy_cross_path = os.path.dirname(mpy_cross.mpy_cross)
if _mpy_cross_path not in os.environ["PATH"]:
    os.environ["PATH"] = os.environ["PATH"] + ":" + _mpy_cross_path


def test_make():
    """Test compilation."""

    with tempfile.TemporaryDirectory() as tmpdir:
        os.system(f"cp -r flash/* {tmpdir}")
        assert os.system(f"make -C {tmpdir}") == 0
        assert os.system(f"make -C {tmpdir} clean") == 0
