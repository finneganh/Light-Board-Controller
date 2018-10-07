# CircuitPython demo - NeoPixel

import time

import board
import busio
import digitalio
import neopixel

from light import Light
from button import Button
from mcp3008 import Mcp3008
from commands import send_light_command, send_at_command, buf_to_string

PROD_MODE = False
LIGHT_MAC_ADDRESS = '907065277A3D' if PROD_MODE else '9C1D588F0605'

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
pixels = neopixel.NeoPixel(
    board.D5, num_buttons, pixel_order=neopixel.RGB, brightness=0.2, auto_write=False)

pixels.fill((0, 0, 0))
pixels.write()

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

toggle_io = digitalio.DigitalInOut(board.A5)
toggle_io.direction = digitalio.Direction.INPUT
toggle_io.pull = digitalio.Pull.UP

LIGHTS = [
    Light(mcp3008, hue_pin=7, brightness_pin=3),
    Light(mcp3008, hue_pin=6, brightness_pin=2),
    Light(mcp3008, hue_pin=5, brightness_pin=1),
    Light(mcp3008, hue_pin=4, brightness_pin=0),
]

PRESET_BUTTONS = [
    Button(board.D11, light=4),
    Button(board.D9, light=2),
    Button(board.D13, light=0),
    Button(board.D10, light=3),
    Button(board.D12, light=1),
]

PRESET_SELECTED_RGB = (255, 0, 255)

VIDEO_LIGHT = 3
STAR_LIGHT = 1

preset_mode_edit = False
current_preset = 255

def update_preset_mode():
    global preset_mode_edit

    preset_mode_edit = not toggle_io.value

def update_current_preset(preset):
    global current_preset

    if current_preset is preset:
        return

    if preset is 255:
        for idx in range(len(LIGHTS)):
            light = LIGHTS[idx]
            light.read()
            send_light_command(btle, COMMAND_SET_LIGHT, [idx, light.hue, light.brightness])

    current_preset = preset

update_preset_mode()


def initBtle():
    # print("Waiting for module ready")
    send_at_command(btle)
    print()

    # print("Getting firmware version")
    # send_at_command('VERSION')
    # print()

    print("Setting central mode")
    send_at_command(btle, 'ROLE1')
    print()


def connect_btle():
    send_at_command(btle, 'CONA' + LIGHT_MAC_ADDRESS)


pressed_btn = 255
cur_movie_light = 0
last_movie_time = 0
movie_delay = 1

def run_connected():
    global preset_mode_edit, pressed_btn, cur_movie_light, last_movie_time, movie_delay

    for idx in range(num_buttons):
        btn = PRESET_BUTTONS[idx]
        val = btn.read()

        if val is 1:
            print("BUTTON PRESS ", idx)
            pressed_btn = idx
        elif val is 2:
            if pressed_btn is idx:
                pressed_btn = 255

        if 0 <= idx < 3:
            if val is 1:
                if preset_mode_edit:
                    cmd = COMMAND_SET_PRESET
                    pixels[PRESET_BUTTONS[idx].light] = (255, 0, 0)
                    pixels.write()
                else:
                    cmd = COMMAND_RUN_PRESET
                    pixels[PRESET_BUTTONS[idx].light] = (255, 255, 255)
                    pixels.write()
                    update_current_preset(idx)

                send_light_command(btle, cmd, [idx])
        if idx == 4 and val is 1 and not preset_mode_edit:
            update_current_preset(4)
            send_light_command(btle, COMMAND_RUN_PRESET, [4])
        if idx == 3 and val is 1 and not preset_mode_edit:
            if current_preset == 3:
                movie_delay = movie_delay * 2.0
                if movie_delay > 8:
                    update_current_preset(255)
            else:
                update_current_preset(3)
                movie_delay = 1
                last_movie_time = 0
                cur_movie_light = -1


    if toggle_io.value == preset_mode_edit:
        update_preset_mode()

    if current_preset == 3 and not preset_mode_edit:
        cur_time = time.monotonic()
        if cur_time > last_movie_time + movie_delay:
            last_movie_time = cur_time
            cur_movie_light = (cur_movie_light + 1) % len(LIGHTS)
            light = LIGHTS[cur_movie_light]
            send_light_command(btle, COMMAND_SET_LIGHT, [255, light.hue, light.brightness])

    for idx in range(len(LIGHTS)):
        light = LIGHTS[idx]
        if light.read():
            if current_preset != 3:
                send_light_command(btle, COMMAND_SET_LIGHT, [idx, light.hue, light.brightness])
                update_current_preset(255)
            elif idx == cur_movie_light:
                send_light_command(btle, COMMAND_SET_LIGHT, [255, light.hue, light.brightness])

    if preset_mode_edit:
        pixels.fill((0, 255, 0))
        pixels[VIDEO_LIGHT] = (0, 0, 0)
        pixels[STAR_LIGHT] = (0, 0, 0)
        if pressed_btn in [0, 1, 2]:
            pixels[PRESET_BUTTONS[pressed_btn].light] = (255, 0, 0)
        
    else:
        pixels.fill((130, 150, 140))
        if current_preset < 255 and current_preset != pressed_btn:
            preset = PRESET_BUTTONS[current_preset]
            pixels[preset.light] = PRESET_SELECTED_RGB

    pixels.write()


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
            pixels.fill((0, 255, 255))
            pixels.write()

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

def test_mcp3008():
    while True:
        print(toggle_io.value)

        time.sleep(1)
