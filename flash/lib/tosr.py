from tosr0x import Tosr0x
from core import Entity
from mainloop import main_loop
import logging


try:
  tosr = Tosr0x()
except Exception as e:
  stdout.buffer.write('n')
  logging.getLogger(__name__).error("Exception: %s", e)
  raise e


class TosrSwitch(Entity):
  def __init__(self, switch_number):
    super().__init__()
    self._switch_number=switch_number
    self._state = self.state
    self._stop_updates = main_loop.schedule_task(lambda: self.update(), period = 30000)

  @property
  def state(self):
    return tosr.get_relay_state(self._switch_number)

  @state.setter
  def state(self, value):
    value = bool(value)
    tosr.set_relay_state(self._switch_number, value)
    if self._state != value:
      self._state = value
      self._run_triggers(value)

  def update(self):
    super().update()
    tosr.update()
    value = self.state
    if self._state != value:
      self._state = value
      self._run_triggers(value)

class TosrTemp(Entity):
  _temp = None

  def __init__(self):
    super().__init__()
    self.update()
    self._stop_updates = main_loop.schedule_task(lambda: self.update(), period = 30000)

  def update(self):
    super().update()
    value = tosr.temperature
    if self._temp != value:
      self._temp = value
      self._run_triggers(value)

  @property
  def state(self):
    return self._temp

  @state.setter
  def state(self, value):
    pass

tosr_switch = {x: TosrSwitch(x) for x in range(5)}
tosr_temp = TosrTemp()

