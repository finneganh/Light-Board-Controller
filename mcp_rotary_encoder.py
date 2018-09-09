import digitalio

class McpRotaryEncoder:
  def __init__(self, pinA, pinB):
    pinA.direction = digitalio.Direction.INPUT
    pinA.pull = digitalio.Pull.UP

    pinB.direction = digitalio.Direction.INPUT
    pinB.pull = digitalio.Pull.UP

    self.pinA = pinA
    self.pinB = pinB

    self.position = 0
    self.lastA = pinA.value
    self.lastB = pinB.value
    print("init at ", self.lastA, self.lastB)

  def update(self): 
    newA = self.pinA.value
    newB = self.pinB.value

    delta = 0

    if self.lastA is False and self.lastB is False:
      if newA is True and newB is False:
        delta = 1
      elif newA is False and newB is True:
        delta = -1

    elif self.lastA is True and self.lastB is False:
      if newA is True and newB is True:
        delta = 1
      elif newA is False and newB is False:
        delta = -1

    elif self.lastA is True and self.lastB is True:
      if newA is False and newB is True:
        delta = 1
      elif newA is True and newB is False:
        delta = -1
    elif self.lastA is False and self.lastB is True:
      if newA is False and newB is False:
        delta = 1
      elif newA is True and newB is True:
        delta = -1

    self.lastA = newA
    self.lastB = newB
    self.position = self.position + delta