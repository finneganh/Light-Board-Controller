import digitalio

class Button:
  last_value = True

  def __init__(self, pin, light):
    self.io = digitalio.DigitalInOut(pin)
    self.io.direction = digitalio.Direction.INPUT
    self.io.pull = digitalio.Pull.UP
    self.light = light

  # Returns 0 if no change, 1 for down, 2 for up
  def read(self):
    cur_value = self.io.value

    if self.last_value is True and cur_value is False:
      out = 1
    elif self.last_value is False and cur_value is True:
      out = 2
    else:
      out = 0

    self.last_value = cur_value

    return out

