"""The machine module to run the tests."""

from unittest.mock import MagicMock

HARD_RESET = 3
PWRON_RESET = 4
WDT_RESET = 5
SOFT_RESET = 6
LOCKUP_RESET = 9
BROWNOUT_RESET = 11

reset_cause = MagicMock(return_value=SOFT_RESET)

soft_reset = MagicMock()

unique_id = MagicMock(return_value=b"\x01\x02\x03\x04\x05\x06\x07\x08")


class Pin:
    """Mock Pin class."""

    IN = 0
    OUT = 1
    ALT = 2
    ANALOG = 3
    DISABLED = 15
    OPEN_DRAIN = 17
    ALT_OPEN_DRAIN = 18
    PULL_UP = 1
    PULL_DOWN = 2
    AF0_COMMISSION = 0
    AF1_SPI_ATTN = 1
    AF2_SPI_SCLK = 2
    AF3_SPI_SSEL = 3
    AF4_SPI_MOSI = 4
    AF5_ASSOC_IND = 5
    AF6_RTS = 6
    AF7_CTS = 7
    AF7_RS485_ENABLE_LOW = 71
    AF7_RS485_ENABLE_HIGH = 135
    AF8_SLEEP_REQ = 8
    AF9_ON_SLEEP = 9
    AF10_RSSI = 10
    AF12_SPI_MISO = 12
    AF13_DOUT = 13
    AF14_DIN = 14
    AF15_SPI_MISO = 15
    AF16_SPI_MOSI = 16
    AF17_SPI_SSEL = 17
    AF18_SPI_SCLK = 18
    AF19_SPI_ATTN = 19

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


class WDT:
    """Mock WDT class."""

    feed = MagicMock(return_value=None)
    init = MagicMock()

    def __init__(self, *args, **kwargs):
        """Save init args."""
        self.init(*args, **kwargs)
