class Light:
  rgb = (0, 0, 0)
  hue = 0
  brightness = 127

  def __init__(self, mcp3008, hue_pin, brightness_pin):
    self.mcp3008 = mcp3008
    self.hue_pin = hue_pin
    self.brightness_pin = brightness_pin

  def read(self):
    # We shift these down to one byte, but then zero out the LSB to reduce
    # noise from the ADC.
    new_hue = (self.mcp3008.read(self.hue_pin) >> 3 & 0b11111110) * 2
    b = self.mcp3008.read(self.brightness_pin)
    new_brightness = (127 - (b >> 3 & 0b11111110)) * 2

    # new_brightness = 63
    if abs(new_hue - self.hue) > 4 or abs(new_brightness - self.brightness) > 4:
      self.hue = new_hue
      self.brightness = new_brightness
      return True

    else:
      return False

