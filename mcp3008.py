import digitalio

class Mcp3008:
  out_buf = bytearray(3)
  in_buf = bytearray(3)

  def __init__(self, spi, cs_pin):
    self.spi = spi

    self.cs = digitalio.DigitalInOut(cs_pin)
    self.cs.direction = digitalio.Direction.OUTPUT
    self.cs.value = True

  def read(self, n):
      self.cs.value = False

      # This byte pattern is from the datasheet. It’s designed to align the value into
      # the last 10 bits of a 3-byte response.

      self.out_buf[0] = 1                      # Start bit
      self.out_buf[1] = 0b10000000 | (n << 4)  # "Single" mode and pin select
      self.out_buf[2] = 0                      # Blank just to give us 8 clock cycles

      self.spi.write_readinto(self.out_buf, self.in_buf)

      self.cs.value = True

      # Value is the last 2 bits of byte 2 and all the bits of byte 3.
      return (self.in_buf[1] & 0b00000011) << 8 | self.in_buf[2]


