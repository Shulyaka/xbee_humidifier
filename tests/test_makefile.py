"""Test Makefile."""

import os


def test_compile():
    """Test compilation."""

    assert os.system("make -C flash") == 0


def test_clean():
    """Test clean-up."""

    assert os.system("make -C flash clean") == 0
