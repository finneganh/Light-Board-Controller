# CircuitPython demo - NeoPixel

import time

import board
import busio
import digitalio

from light import Light
from preset import Preset

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

# Default baud rate for the board is 9600. We keep a low-ish timeout so we can determine
# there’s no content in 50ms.
btle = busio.UART(board.TX, board.RX, baudrate=9600, timeout=50)

statusLed = digitalio.DigitalInOut(board.D13)
statusLed.direction = digitalio.Direction.OUTPUT
statusLed.value = False

statusIo = digitalio.DigitalInOut(board.D7)
statusIo.direction = digitalio.Direction.INPUT
statusIo.pull = digitalio.Pull.DOWN

light1 = Light(huePin=board.A5, brightnessPin=board.A4)
LIGHTS = [
    light1,
    light1,
]

PRESETS = [
    Preset(showPin=board.D11, setPin=board.D10)
]

def bufToString(data):
    if data is None:
        return ''
    else:
        return ''.join([chr(b) for b in data])

def sendAtCommand(cmd=False):
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
            response = bufToString(data)
            print(response, end='')

            if response.startswith('ERR'):
                lastCommandTime = 0
            else:
                gotResponse = True


def sendLightCommand(cmd, params, extraParams = []):
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
        elif time.time() > lastCommandTime + 2 or not statusIo.value:
            return False


def initBtle():
    print("Waiting for module ready")
    sendAtCommand()
    print()

    print("Getting firmware version")
    sendAtCommand('VERSION')
    print()

    print("Setting central mode")
    sendAtCommand('ROLE1')
    print()


def connectBtle():
    sendAtCommand('CONA' + LIGHT_MAC_ADDRESS)

def scanControls():
    for i, l in enumerate(LIGHTS):
        changed = l.read()
        if changed:
            sendLightCommand(COMMAND_SET_LIGHT, [i], l.rgb)

    for i, p in enumerate(PRESETS):
        action = p.read()
        if action is 1:
            sendLightCommand(COMMAND_RUN_PRESET, [i])
        elif action is 2:
            sendLightCommand(COMMAND_SET_PRESET, [i])

def main():
    print("Controller started")

    if statusIo.value:
        print("Bluetooth already connected")
        state = STATE_CONNECTED
    else:
        state = STATE_UNINITIALIZED

    while True:
        if statusIo.value:
            if state is not STATE_CONNECTED and state is not STATE_WAITING_CONNECTION:
                print("State change: CONNECTED")
                state = STATE_CONNECTED
                print()
        else:
            if state is STATE_CONNECTED:
                print("State change: DISCONNECTED")
                state = STATE_DISCONNECTED
                print()

        statusLed.value = state is STATE_CONNECTED

        if state is STATE_CONNECTED:
            scanControls()

        elif state is STATE_DISCONNECTED:
            print("Starting connection")
            connectBtle()
            state = STATE_WAITING_CONNECTION

        elif state is STATE_WAITING_CONNECTION:
            dataStr = bufToString(btle.read(20))
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
