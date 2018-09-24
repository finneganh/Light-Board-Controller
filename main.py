# CircuitPython demo - NeoPixel

import time

import board
import busio
import digitalio
import neopixel

from light import Light
from button import Button
from mcp3008 import Mcp3008

LIGHT_MAC_ADDRESS = '907065277A3D'

COMMAND_PREFIX = 0xF0
COMMAND_GET_STATUS = 0x10
COMMAND_SET_LIGHT = 0x20
COMMAND_SET_ALL = 0x21
COMMAND_RUN_PRESET = 0x30
COMMAND_SET_PRESET = 0x31

STATE_DISCONNECTED = 0
STATE_CONNECTED = 1
STATE_UNINITIALIZED = 2
STATE_WAITING_CONNECTION = 3

num_buttons = 5
button_pixels = neopixel.NeoPixel(
    board.D5, num_buttons, pixel_order=neopixel.RGB, brightness=0.2, auto_write=False)

# Default baud rate for the board is 9600. We keep a low-ish timeout so we can determine
# there’s no content in 50ms.
btle = busio.UART(board.TX, board.RX, baudrate=9600, timeout=50)

btle_status_io = digitalio.DigitalInOut(board.D7)
btle_status_io.direction = digitalio.Direction.INPUT
btle_status_io.pull = digitalio.Pull.DOWN

spi = busio.SPI(board.SCK, MISO=board.MISO, MOSI=board.MOSI)
spi.try_lock()
spi.configure(baudrate=1200000, phase=0, polarity=0)

mcp3008 = Mcp3008(spi, cs_pin=board.D2)

light1 = Light(mcp3008, hue_pin=0, brightness_pin=1)
LIGHTS = [
    light1,
]

PRESET_BUTTONS = [
    Button(board.D9, light=2),
    Button(board.D10, light=1),
    Button(board.D11, light=0),
    Button(board.D12, light=3),
    Button(board.D13, light=4),
]

button_states = [
    0,
    0,
    0,
    0,
    0,
]

RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)

COLORS = [
    RED,
    YELLOW,
    GREEN,
    CYAN,
    BLUE,
    PURPLE
]

def buf_to_string(data):
    if data is None:
        return ''
    else:
        return ''.join([chr(b) for b in data])


def send_at_command(cmd=False):
    gotResponse = False
    lastCommandTime = 0

    while True:
        if time.time() > lastCommandTime + 2:
            if cmd:
                str = 'AT+' + cmd
            else:
                str = 'AT'

            print(str)
            btle.write(str + '\r\n')

            lastCommandTime = time.time()

        data = btle.read(32)

        if data is None or len(data) is 0:
            if gotResponse:
                return
        else:
            response = buf_to_string(data)
            print(response, end='')

            if response.startswith('ERR'):
                lastCommandTime = 0
            else:
                gotResponse = True


def send_light_command(cmd, params, extraParams=[]):
    cmd = [COMMAND_PREFIX, cmd]
    cmd.extend(params)
    cmd.extend(extraParams)

    # Pad out to 20 bytes because that's the BTLE limit
    cmd += [0] * (20 - len(cmd))

    btle.write(bytes(cmd))

    lastCommandTime = time.time()

    while True:
        data = btle.read(20)

        if data is not None:
            return True
        elif time.time() > lastCommandTime + 2 or not btle_status_io.value:
            return False


def initBtle():
    print("Waiting for module ready")
    send_at_command()
    print()

    print("Getting firmware version")
    send_at_command('VERSION')
    print()

    print("Setting central mode")
    send_at_command('ROLE1')
    print()


def connect_btle():
    send_at_command('CONA' + LIGHT_MAC_ADDRESS)


def run_connected():
    btn_changed = False
    for idx in range(num_buttons):
        btn = PRESET_BUTTONS[idx]
        if btn.read():
            button_states[idx] = (button_states[idx] + 1) % len(COLORS)
            btn_changed = True

        button_pixels[btn.light] = COLORS[button_states[idx]]

    if btn_changed:
        button_pixels.write()

    for light in LIGHTS:
        if light.read():
            button_pixels.fill(light.rgb)
            button_pixels.write()
            send_light_command(COMMAND_SET_LIGHT, [1], light.rgb)

def main():
    print("Controller started")

    if btle_status_io.value:
        print("Bluetooth already connected")
        state = STATE_CONNECTED
    else:
        state = STATE_UNINITIALIZED

    while True:
        if btle_status_io.value:
            if state is not STATE_CONNECTED and state is not STATE_WAITING_CONNECTION:
                print("State change: CONNECTED")
                state = STATE_CONNECTED
                print()
        else:
            if state is STATE_CONNECTED:
                print("State change: DISCONNECTED")
                state = STATE_DISCONNECTED
                print()

        if state is STATE_CONNECTED:
            run_connected()

        elif state is STATE_DISCONNECTED:
            print("Starting connection")
            connect_btle()
            state = STATE_WAITING_CONNECTION

        elif state is STATE_WAITING_CONNECTION:
            dataStr = buf_to_string(btle.read(20))
            print(dataStr, end='')

            if dataStr.startswith('+Connected'):
                state = STATE_DISCONNECTED
                # Clear out any existing content
                while btle.read(1) is not None:
                    pass

        elif state is STATE_UNINITIALIZED:
            print("Initializing Bluetooth module:")
            initBtle()
            state = STATE_DISCONNECTED



main()
