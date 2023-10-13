"""The os module to run tests."""

from unittest.mock import MagicMock

chdir = MagicMock()
getcwd = MagicMock()
compile = MagicMock()  # noqa: PBP113
remove = MagicMock()
sync = MagicMock()
bundle = MagicMock()
listdir = MagicMock()
listdir.return_value = []
