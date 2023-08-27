"""The gc mock module to speed up the tests."""

from unittest.mock import MagicMock

collect = MagicMock()
mem_alloc = MagicMock(return_value=20000)
mem_free = MagicMock(return_value=12000)
