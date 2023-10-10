"""Micropython TOSR04 interface implementation."""

from sys import stdin, stdout
from time import sleep_ms, ticks_diff, ticks_ms

from xbee import atcmd


class Tosr0x:
    """Class implementing tosr protocol."""

    _states = 0
    _lastupdate = None

    def __init__(self):
        """Init the class."""
        Tosr0x.tosr0x_reset()

    def tosr0x_reset():
        """Close all switches."""
        atcmd("AP", 4)
        sleep_ms(200)
        stdout.buffer.write("n")
        stdin.buffer.read()

    def _read(cmd=None, n=1, timeout=100, retry=1):
        """Read serial data, returns less data on timeout, may return more than requested if there is more data in read buffer."""
        for _ in range(retry):
            if cmd is not None:
                stdin.buffer.read()
                stdout.buffer.write(cmd)
            data = b""
            now = ticks_ms()
            while len(data) < n and ticks_diff(ticks_ms(), now) <= timeout:
                r = stdin.buffer.read()
                if r is not None:
                    data += r
            if len(data) == n:
                break
        return data

    def set_relay_state(self, switch_number, state):
        """Update relay state."""
        state = bool(state)
        current_state = ~state
        iteration = 0
        while current_state != state:
            if iteration >= 10:
                raise RuntimeError("Failed to update relay state")
            iteration = iteration + 1
            stdout.buffer.write(
                ("defghijkl" if state else "nopqrstuv")[
                    switch_number : switch_number + 1
                ]
            )
            self._lastupdate = None
            self.update()
            if switch_number:
                current_state = self.get_relay_state(switch_number)
            elif state:
                current_state = (
                    self.get_relay_state(1)
                    & self.get_relay_state(2)
                    & self.get_relay_state(3)
                    & self.get_relay_state(4)
                )
            else:
                current_state = self.get_relay_state(0)

    def get_relay_state(self, switch_number):
        """Get cached relay state."""
        return (
            bool(self._states & (2 ** (switch_number - 1)))
            if switch_number
            else bool(self._states & 0xF)
        )

    def update(self):
        """Update the switch states, ratelimited."""
        if self._lastupdate is None or ticks_diff(ticks_ms(), self._lastupdate) >= 300:
            data = Tosr0x._read("[", 1, retry=10)
            if len(data) != 1:
                raise RuntimeError("Failed to get relay state: {}".format(data))
            self._states = int.from_bytes(data, "big")
            self._lastupdate = ticks_ms()

    @property
    def temperature(self):
        """Read TOSR0-T temperature."""
        data = Tosr0x._read("a", 2, retry=10)
        if len(data) != 2:
            raise RuntimeError("Failed to get temperature: {}".format(data))

        temp = int.from_bytes(data, "big")
        return (temp / 16 - 4096) if temp > 32767 else (temp / 16)


def tosr0x_version():
    """Verify TOSR0X presence. Returns firmware version number if found, None if TOSR0X not detected."""
    Tosr0x.tosr0x_reset()
    for _ in range(10):
        data = Tosr0x._read("Z", 2)
        if data[0:1] == b"\x0f":
            return int.from_bytes(data[1:2], "big")
        sleep_ms(500)
    return None
