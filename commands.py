import time

COMMAND_PREFIX = 0xF0

def buf_to_string(data):
    if data is None:
        return ''
    else:
        return ''.join([chr(b) for b in data])


def send_at_command(btle, cmd=False):
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


def send_light_command(btle, cmd, params):
    cmd = [COMMAND_PREFIX, cmd]
    cmd.extend(params)

    # Pad out to 20 bytes because that's the BTLE limit. We fill up to
    # this amount to (hopefully) cause an immediate write, rather than
    # worry about something getting to a timeout.
    cmd += [0] * (20 - len(cmd))

    btle.write(bytes(cmd))

    lastCommandTime = time.time()

    while True:
        data = btle.read(20)

        if data is not None:
            return True
        elif time.time() > lastCommandTime + 2:
            return False


