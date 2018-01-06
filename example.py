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
        print(device)


def example():
    state = load_state()

    # Get the URLs for the API.
    if 'oauth_base' not in state and 'api_root' not in state:
        gw = wideq.gateway_info()
        state['oauth_base'] = gw['empUri']
        state['api_root'] = gw['thinqUri']
        save_state(state)
    oauth_base = state['oauth_base']
    api_root = state['api_root']

    # If we don't have an access token, authenticate.
    if 'access_token' not in state:
        login_url = wideq.oauth_url(oauth_base)
        print('Log in here:')
        print(login_url)
        print('Then paste the URL where the browser is redirected:')
        callback_url = input()
        state['access_token'] = wideq.parse_oauth_callback(callback_url)
        save_state(state)
    access_token = state['access_token']

    # If we don't have a session, log in.
    if 'session_id' not in state:
        session_info = wideq.login(api_root, access_token)
        state['session_id'] = session_info['jsessionId']
        save_state(state)
        print_devices(session_info['item'])
    session_id = state['session_id']

    # Request a list of devices.
    devices = wideq.get_devices(api_root, access_token, session_id)
    print(devices)


if __name__ == '__main__':
    example()
