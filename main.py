# CircuitPython demo - NeoPixel

import time

import board
import busio
import digitalio

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

statusPin = digitalio.DigitalInOut(board.D7)
statusPin.direction = digitalio.Direction.INPUT
statusPin.pull = digitalio.Pull.DOWN

def bufToString(data):
    if data is None:
        return ''
    else:
        return ''.join([chr(b) for b in data])

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

def sendAtCommand(cmd = False):
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

def sendLightCommand(cmd, params, extraParams):
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
        elif time.time() > lastCommandTime + 2 or not statusPin.value:
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

def main():
    print("Controller started")

    if statusPin.value:
        print("Bluetooth already connected")
        state = STATE_CONNECTED
    else:
        state = STATE_UNINITIALIZED

    while True:
        if statusPin.value:
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
            pos = int(time.monotonic() * 20)
            sendLightCommand(COMMAND_SET_LIGHT, [0], wheel(pos & 255))
            sendLightCommand(COMMAND_SET_LIGHT, [1], wheel((pos + 127) & 255))

        elif state is STATE_DISCONNECTED:
            print("Starting connection")
            connectBtle()
            state = STATE_WAITING_CONNECTION

        elif state is STATE_WAITING_CONNECTION:
            dataStr = bufToString(btle.read(20))
            print(dataStr, end = '')

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