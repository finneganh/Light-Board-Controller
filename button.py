import digitalio

class Button:
  last_value = True

  def __init__(self, pin, light):
    self.io = digitalio.DigitalInOut(pin)
    self.io.direction = digitalio.Direction.INPUT
    self.io.pull = digitalio.Pull.UP
    self.light = light

  def read(self):
    out = False

    if self.last_value is True and self.io.value is False:
      out = True

    self.last_value = self.io.value

    return out

