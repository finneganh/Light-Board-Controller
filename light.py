# Derived from: http://www.easyrgb.com/en/math.php#text2
#
# Input range: 0–1
# Output range: 0—255
def hsl2rgb(h, s, l):
  if s is 0:
    r = l * 255
    g = l * 255
    b = l * 255
  
  else:
    if l < 0.5:
      v2 = l * (1 + s)
    else:
      v2 = (l + s) - (s * l)

    v1 = 2 * l - v2

    r = 255 * hue2rgb(v1, v2, h + 0.33333)
    g = 255 * hue2rgb(v1, v2, h)
    b = 255 * hue2rgb(v1, v2, h - 0.33333)

  return (int(r), int(g), int(b))

def hue2rgb(v1, v2, vh):
  if vh < 0:
    vh += 1

  if vh > 1:
    vh -= 1
  
  if vh * 6 < 1:
    return v1 + (v2 - v1) * 6 * vh

  if vh * 2 < 1:
    return v2
  
  if vh * 3 < 2:
    return v1 + (v2 - v1) * (0.666666 - vh) * 6

  return v1

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
    new_hue = self.mcp3008.read(self.hue_pin) >> 2 & 0b11111110
    new_brightness = self.mcp3008.read(self.brightness_pin) >> 2 & 0b11111110
    new_brightness = 127

    if new_hue != self.hue or new_brightness != self.brightness:
      self.hue = new_hue
      self.brightness = new_brightness
      self.rgb = hsl2rgb(new_hue / 255, 1.0, new_brightness / 255)
      return True

    else:
      return False

