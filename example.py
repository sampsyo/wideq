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


def authenticate(gateway):
    login_url = gateway.oauth_url()
    print('Log in here:')
    print(login_url)
    print('Then paste the URL where the browser is redirected:')
    callback_url = input()
    access_token = wideq.parse_oauth_callback(callback_url)
    return wideq.Auth(gateway, access_token)


def get_session(state, reauth=False):
    """Get a Session object we can use to make API requests.

    By default, try to use credentials from `state`. If `reauth` if
    true, instead force re-authentication.

    Return the Session and, if they came along with session creation,
    the information about the user's devices.
    """

    # Get the gateway, which contains the base URLs and hostnames for
    # accessing the API.
    if 'gateway' in state:
        gateway = wideq.Gateway.load(state['gateway'])
    else:
        print('Discovering gateway servers.')
        gateway = wideq.Gateway.discover()

        state['gateway'] = gateway.dump()
        save_state(state)

    # Authenticate the user.
    if 'auth' in state and not reauth:
        auth = wideq.Auth.load(gateway, state['auth'])
        new_auth = False
    else:
        auth = authenticate(gateway)
        new_auth = True

        state['auth'] = auth.dump()
        save_state(state)

    # Start a session.
    if 'session' in state and not new_auth:
        session = wideq.Session.load(auth, state['session'])
        devices = None
    else:
        print('Starting session.')
        session, devices = auth.start_session()

        state['session'] = session.dump()
        save_state(state)

    return session, devices


def example():
    state = load_state()

    session, devices = get_session(state)

    try:
        # Request a list of devices, if we didn't get them "for free"
        # already by starting the session.
        if not devices:
            devices = session.get_devices()

    except wideq.NotLoggedInError:
        print('Session expired.')
        return

    print_devices(devices)


if __name__ == '__main__':
    example()
