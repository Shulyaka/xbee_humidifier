"""Micro python TOSR04 interface implementation."""

from sys import stdin, stdout
from time import sleep, ticks_ms

class Tosr0x:

  _states = 0
  _lastupdate = None

  def __init__(self):
    stdout.buffer.write('n')

  def set_relay_state(self, switch_number, state):
    state = bool(state)
    current_state = ~state
    iteration = 0
    while current_state != state:
      if iteration >= 10:
        raise RuntimeError('Failed to update relay state')
      elif iteration:
        sleep(1)
      iteration = iteration + 1
      stdout.buffer.write(('defghijkl' if state else 'nopqrstuv')[switch_number:switch_number+1])
      self.update()
      if switch_number:
        current_state = self.get_relay_state(switch_number)
      elif state:
        current_state = self.get_relay_state(1) & self.get_relay_state(2) & self.get_relay_state(3) & self.get_relay_state(4)
      else:
        current_state = self.get_relay_state(0)

  def get_relay_state(self, switch_number):
    return bool(self._states & (2**(switch_number-1))) if switch_number else bool(self._states & 0xF)

  def update(self):
    now = ticks_ms()
    if self._lastupdate is None or now - self._lastupdate >= 300:
      _ = stdin.buffer.read()
      stdout.buffer.write('[')
      self._states = int.from_bytes(stdin.buffer.read(1), "big")
      self._lastupdate = now

  @property
  def temperature(self):
    _ = stdin.buffer.read()
    stdout.buffer.write('a')
    temp = int.from_bytes(stdin.buffer.read(2), "big")
    return (temp / 16 - 4096) if temp > 32767 else (temp / 16)

  @property
  def switch0(self):
    return self.get_relay_state(0)

  @switch0.setter
  def switch0(self, state):
    self.set_relay_state(0, state)

  @property
  def switch1(self):
    return self.get_relay_state(1)

  @switch1.setter
  def switch1(self, state):
    self.set_relay_state(1, state)
    
  @property
  def switch2(self):
    return self.get_relay_state(2)

  @switch2.setter
  def switch2(self, state):
    self.set_relay_state(2, state)    

  @property
  def switch3(self):
    return self.get_relay_state(3)

  @switch3.setter
  def switch3(self, state):
    self.set_relay_state(3, state)

  @property
  def switch4(self):
    return self.get_relay_state(4)

  @switch4.setter
  def switch4(self, state):
    self.set_relay_state(4, state)
