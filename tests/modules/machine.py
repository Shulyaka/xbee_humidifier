"""The machine module to run the tests."""

from unittest.mock import MagicMock

soft_reset = MagicMock()


class Pin:
    """Mock Pin class."""

    IN = 0
    OUT = 1
    PULL_UP = 1
    value = MagicMock(return_value=False)
    init = MagicMock()

    def __init__(self, *args, **kwargs):
        """Save init args."""
        self.init(*args, **kwargs)


class PWM:
    """Mock PWM class."""

    duty = MagicMock(return_value=0)
    init = MagicMock()

    def __init__(self, *args, **kwargs):
        """Save init args."""
        self.init(*args, **kwargs)


class ADC:
    """Mock ADC class."""

    read = MagicMock(return_value=0)
    init = MagicMock()

    def __init__(self, *args, **kwargs):
        """Save init args."""
        self.init(*args, **kwargs)
