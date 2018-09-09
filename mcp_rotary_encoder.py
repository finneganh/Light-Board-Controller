class McpRotaryEncoder:
  def __init__(self, a, b):
    self.pinAMask = 1 << a
    self.pinBMask = 1 << b

    self.position = 0
    self.lastA = None
    self.lastB = None

  def update(self, gpio): 
    newA = (gpio & self.pinAMask) != 0
    newB = (gpio & self.pinBMask) != 0

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