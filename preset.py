import digitalio

class Preset:
  lastShowValue = True
  lastSetValue = True

  def __init__(self, showPin, setPin):
    self.showIo = digitalio.DigitalInOut(showPin)
    self.showIo.direction = digitalio.Direction.INPUT
    self.showIo.pull = digitalio.Pull.UP

    self.setIo = digitalio.DigitalInOut(setPin)
    self.setIo.direction = digitalio.Direction.INPUT
    self.setIo.pull = digitalio.Pull.UP

  def read(self):
    out = False

    if self.lastShowValue is False and self.showIo.value is True:
      out = 1
    elif self.lastSetValue is False and self.setIo.value is True:
      out = 2

    self.lastShowValue = self.showIo.value
    self.lastSetValue = self.setIo.value

    return out

