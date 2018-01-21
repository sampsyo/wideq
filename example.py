import wideq
import json
import time
import sys

STATE_FILE = 'wideq_state.json'


def load_state():
    """Load the current state data for this example.
    """

    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except IOError:
        return {}


def save_state(state):
    """Dump the current state to disk.
    """

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)


def authenticate(gateway):
    login_url = gateway.oauth_url()
    print('Log in here:')
    print(login_url)
    print('Then paste the URL where the browser is redirected:')
    callback_url = input()
    return wideq.Auth.from_url(gateway, callback_url)


def example_command(client, args):
    if not args or args[0] == 'ls':
        for device in client.devices:
            print('{deviceId}: {alias} ({modelNm})'.format(**device))

    elif args[0] == 'mon':
        device_id = args[1]

        with wideq.Monitor(client.session, device_id) as mon:
            try:
                while True:
                    time.sleep(1)
                    print('Polling...')
                    res = mon.poll()
                    if res:
                        print('setting: {}°C'.format(res['TempCfg']))
                        print('current: {}°C'.format(res['TempCur']))

            except KeyboardInterrupt:
                pass

    elif args[0] == 'set-temp':
        temp = args[1]
        device_id = args[2]

        client.session.set_device_controls(device_id, {'TempCfg': temp})


def example(args):
    state = load_state()
    client = wideq.Client.load(state)

    if not client._auth:
        client._auth = authenticate(client.gateway)

    # Loop to retry if session has expired.
    while True:
        try:
            example_command(client, args)
            break

        except wideq.NotLoggedInError:
            print('Session expired.')
            client.refresh()

    save_state(client.dump())


if __name__ == '__main__':
    example(sys.argv[1:])
