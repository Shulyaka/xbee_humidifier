"""Micropython TOSR04 interface implementation."""

from sys import stdin, stdout
from time import ticks_ms


class Tosr0x:
    """Class implementing tosr protocol."""

    _states = 0
    _lastupdate = None

    def __init__(self):
        """Init the class."""
        Tosr0x.tosr0x_reset()

    def tosr0x_reset():
        """Close all switches."""
        stdout.buffer.write("n")

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
        now = ticks_ms()
        if self._lastupdate is None or now - self._lastupdate >= 300:
            stdin.buffer.read()
            stdout.buffer.write("[")
            char = None
            while char is None or len(char) != 1:
                if ticks_ms() - now > 1000:
                    raise RuntimeError("Failed to get relay state")
                char = stdin.buffer.read()
                if char is not None and len(char) > 1:
                    raise RuntimeError("Unexpected data received")
            self._states = int.from_bytes(char, "big")
            self._lastupdate = ticks_ms()

    @property
    def temperature(self):
        """Read TOSR0-T temperature."""
        stdin.buffer.read()
        stdout.buffer.write("a")
        now = ticks_ms()
        char = b""
        while char is None or len(char) != 2:
            if ticks_ms() - now > 1000:
                raise RuntimeError("Failed to get temperature")
            newchar = stdin.buffer.read()
            if newchar is not None:
                char += newchar
            if char is not None and len(char) > 2:
                raise RuntimeError("Unexpected data received")

        temp = int.from_bytes(char, "big")
        return (temp / 16 - 4096) if temp > 32767 else (temp / 16)

    @property
    def switch0(self):
        """Get all switches."""
        return self.get_relay_state(0)

    @switch0.setter
    def switch0(self, state):
        """Set all switches."""
        self.set_relay_state(0, state)

    @property
    def switch1(self):
        """Get switch 1."""
        return self.get_relay_state(1)

    @switch1.setter
    def switch1(self, state):
        """Set switch 1."""
        self.set_relay_state(1, state)

    @property
    def switch2(self):
        """Get switch 2."""
        return self.get_relay_state(2)

    @switch2.setter
    def switch2(self, state):
        """Set switch 2."""
        self.set_relay_state(2, state)

    @property
    def switch3(self):
        """Get switch 3."""
        return self.get_relay_state(3)

    @switch3.setter
    def switch3(self, state):
        """Set switch 3."""
        self.set_relay_state(3, state)

    @property
    def switch4(self):
        """Get switch 4."""
        return self.get_relay_state(4)

    @switch4.setter
    def switch4(self, state):
        """Set switch 4."""
        self.set_relay_state(4, state)
