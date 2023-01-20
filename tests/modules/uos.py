"""The os module to run tests."""

from unittest.mock import MagicMock

chdir = MagicMock()
compile = MagicMock()
remove = MagicMock()
sync = MagicMock()
bundle = MagicMock()
listdir = MagicMock()
listdir.return_value = []
