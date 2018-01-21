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


class Client(object):
    """A higher-level API wrapper that provides a session.
    """

    def __init__(self):
        # The three steps required to get access to call the API.
        self._gateway = None
        self._auth = None
        self._session = None

        # The last list of devices we got from the server.
        self._devices = None

    @property
    def gateway(self):
        if not self._gateway:
            self._gateway = wideq.Gateway.discover()
        return self._gateway

    @property
    def auth(self):
        if not self._auth:
            assert False, "unauthenticated"
        return self._auth

    @property
    def session(self):
        if not self._session:
            self._session, self._devices = self.auth.start_session()
        return self._session

    @property
    def devices(self):
        if not self._devices:
            self._devices = self.session.get_devices()
        return self._devices

    def load(self, state):
        """Load the client objects from the encoded state data.
        """

        if 'gateway' in state:
            self._gateway = wideq.Gateway.load(state['gateway'])

        if 'auth' in state:
            self._auth = wideq.Auth.load(self._gateway, state['auth'])

        if 'session' in state:
            self._session = wideq.Session.load(self._auth, state['session'])

    def dump(self):
        """Serialize the client state."""

        out = {}
        if self._gateway:
            out['gateway'] = self._gateway.dump()
        if self._auth:
            out['auth'] = self._auth.dump()
        if self._session:
            out['session'] = self._session.dump()
        return out

    def refresh(self):
        self._auth = self.auth.refresh()
        self._session, self._devices = self.auth.start_session()


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

        client.session.set_device_controls(device_id,
                                           {'TempCfg': temp})


def example(args):
    state = load_state()
    client = Client()
    client.load(state)

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
