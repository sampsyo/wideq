import wideq
import json

STATE_FILE = 'wideq_state.json'


class Memo(object):
    """Store memoization data persistently in a JSON file.
    """

    def __init__(self, filename):
        self.filename = filename
        self.load()

    def load(self):
        """Load the current memoization data."""
        try:
            with open(self.filename) as f:
                self.state = json.load(f)
        except IOError:
            self.state = {}

    def save(self):
        """Dump the current state to disk."""
        with open(self.filename, 'w') as f:
            json.dump(self.state, f)

    def call(self, fn, key=None):
        """Call a function using memoization.

        You can either specify a memoization key explicitly or, by
        default, use the function's `__name__`.
        """

        key = key or fn.__name__
        if key in self.state:
            return self.state[key]
        else:
            ret = fn()
            self.state[key] = ret
            self.save()
            return ret


def print_devices(devices):
    for device in devices:
        print(device['alias'])


def endpoints():
    gw = wideq.gateway_info()
    return {
        'oauth_base': gw['empUri'],
        'api_root': gw['thinqUri'],
    }


def login(oauth_base):
    login_url = wideq.oauth_url(oauth_base)
    print('Log in here:')
    print(login_url)
    print('Then paste the URL where the browser is redirected:')
    callback_url = input()
    return wideq.parse_oauth_callback(callback_url)


def start_session(api_root, access_token):
    session_info = wideq.login(api_root, access_token)
    print_devices(session_info['item'])
    return session_info['jsessionId']


def example():
    memo = Memo(STATE_FILE)

    # Get the URLs for the API.
    ep = memo.call(endpoints)
    oauth_base = ep['oauth_base']
    api_root = ep['api_root']

    # Authenticate to get an access token.
    access_token = memo.call(lambda: login(oauth_base), 'access_token')

    # If we don't have a session, log in.
    session_id = memo.call(lambda: start_session(api_root, access_token),
                           'session_id')

    # Request a list of devices.
    devices = wideq.get_devices(api_root, access_token, session_id)
    print_devices(devices)


if __name__ == '__main__':
    example()
