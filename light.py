import analogio

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if (pos < 0) or (pos > 255):
        return (0, 0, 0)
    if pos < 85:
        return (int(pos * 3), int(255 - (pos * 3)), 0)
    elif pos < 170:
        pos -= 85
        return (int(255 - pos * 3), 0, int(pos * 3))
    else:
        pos -= 170
        return (0, int(pos * 3), int(255 - pos * 3))

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

  def __init__(self, huePin, brightnessPin):
    self.hueIo = analogio.AnalogIn(huePin)
    self.brightnessIo = analogio.AnalogIn(brightnessPin)

  def read(self):
    hue = int(self.hueIo.value / 655.360) / 100
    brightness = int(self.brightnessIo.value / 655.360) / 100

    newRgb = hsl2rgb(hue, 1.0, brightness)
    if newRgb != self.rgb:
      self.rgb = newRgb
      return True

    else:
      return False
