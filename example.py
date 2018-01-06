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


def example():
    state = load_state()

    # Get the URLs for the API.
    if 'oauth_base' not in state and 'api_root' not in state:
        gw = wideq.gateway_info()
        state['oauth_base'] = gw['empUri']
        state['api_root'] = gw['thinqUri']
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
    access_token = state['access_token']

    # If we don't have a session, log in.
    if 'session_id' not in state:
        session_info = wideq.login(api_root, access_token)
        print(session_info)


if __name__ == '__main__':
    example()
