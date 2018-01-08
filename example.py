import wideq
import json

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


def print_devices(devices):
    for device in devices:
        print(device['alias'])


class Gateway(object):
    def __init__(self, oauth_base, api_root):
        self.oauth_base = oauth_base
        self.api_root = api_root

    @classmethod
    def discover(cls):
        gw = wideq.gateway_info()
        return cls(gw['empUri'], gw['thinqUri'])

    @classmethod
    def load(cls, data):
        return cls(data['oauth_base'], data['api_root'])

    def dump(self):
        return {'oauth_base': self.oauth_base, 'api_root': self.api_root}

    def oauth_url(self):
        return wideq.oauth_url(self.oauth_base)


class Auth(object):
    def __init__(self, gateway, access_token):
        self.gateway = gateway
        self.access_token = access_token

    def start_session(self):
        """Start an API session for the logged-in user. Return the
        Session object and the user's devices.
        """

        session_info = wideq.login(self.gateway.api_root, self.access_token)
        session_id = session_info['jsessionId']
        return Session(self, session_id), session_info['item']

    def dump(self):
        return self.access_token

    @classmethod
    def load(cls, gateway, data):
        return cls(gateway, data)


class Session(object):
    def __init__(self, auth, session_id):
        self.auth = auth
        self.session_id = session_id

    def get_devices(self):
        return wideq.get_devices(self.auth.gateway.api_root,
                                 self.auth.access_token,
                                 self.session_id)

    def dump(self):
        return self.session_id

    @classmethod
    def load(cls, auth, data):
        return cls(auth, data)


def authenticate(gateway):
    login_url = gateway.oauth_url()
    print('Log in here:')
    print(login_url)
    print('Then paste the URL where the browser is redirected:')
    callback_url = input()
    access_token = wideq.parse_oauth_callback(callback_url)
    return Auth(gateway, access_token)


def example():
    state = load_state()

    # Get the gateway, which contains the base URLs and hostnames for
    # accessing the API.
    if 'gateway' in state:
        gateway = Gateway.load(state['gateway'])
    else:
        gateway = Gateway.discover()

        state['gateway'] = gateway.dump()
        save_state(state)

    # Authenticate the user.
    if 'auth' in state:
        auth = Auth.load(gateway, state['auth'])
    else:
        auth = authenticate(gateway)

        state['auth'] = auth.dump()
        save_state(state)

    # Start a session.
    if 'session' in state:
        session = Session.load(auth, state['session'])
        devices = None
    else:
        session, devices = auth.start_session()

        state['session'] = session.dump()
        save_state(state)

    # Request a list of devices, if we didn't get them "for free"
    # already by starting the session.
    if not devices:
        devices = session.get_devices()

    print_devices(devices)


if __name__ == '__main__':
    example()
