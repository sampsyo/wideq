import requests
from urllib.parse import urljoin, urlencode, urlparse, parse_qs


GATEWAY_URL = 'https://kic.lgthinq.com:46030/api/common/gatewayUriList'
APP_KEY = 'wideq'
SECURITY_KEY = 'nuts_securitykey'
DATA_ROOT = 'lgedmRoot'
COUNTRY = 'US'
LANGUAGE = 'en-US'
SVC_CODE = 'SVC202'
CLIENT_ID = 'LGAO221A02'

OAUTH_PATH = 'login/sign_in'
LOGIN_PATH = 'member/login'
DEVICE_LIST_PATH = 'device/deviceList'


def lgedm_post(url, data=None, access_token=None, session_id=None):
    """Make an HTTP request in the format used by the API servers.

    In this format, the request POST data sent as JSON under a special
    key; authentication sent in headers. Return the JSON data extracted
    from the response.

    The `access_token` and `session_id` are required for most normal,
    authenticated requests. They are not required, for example, to load
    the gateway server data or to start a session.
    """

    headers = {
        'x-thinq-application-key': APP_KEY,
        'x-thinq-security-key': SECURITY_KEY,
        'Accept': 'application/json',
    }
    if access_token:
        headers['x-thinq-token'] = access_token
    if session_id:
        headers['x-thinq-jsessionId'] = session_id

    res = requests.post(url, json={DATA_ROOT: data}, headers=headers)
    return res.json()[DATA_ROOT]


def gateway_info():
    """Load information about the hosts to use for API interaction.
    """

    return lgedm_post(
        GATEWAY_URL,
        {'countryCode': COUNTRY, 'langCode': LANGUAGE},
    )


def oauth_url(oauth_base):
    """Construct the URL for users to log in (in a browser) to start an
    authenticated session.
    """

    url = urljoin(oauth_base, OAUTH_PATH)
    query = urlencode({
        'country': COUNTRY,
        'language': LANGUAGE,
        'svcCode': SVC_CODE,
        'authSvr': 'oauth2',
        'client_id': CLIENT_ID,
        'division': 'ha',
        'grant_type': 'password',
    })
    return '{}?{}'.format(url, query)


def parse_oauth_callback(url):
    """Parse the URL to which an OAuth login redirected to obtain an
    access token for API credentials.
    """

    params = parse_qs(urlparse(url).query)
    return params['access_token'][0]


def login(api_root, access_token):
    """Use an access token to log into the API and obtain a session and
    return information about the session.
    """

    url = urljoin(api_root + '/', LOGIN_PATH)
    data = {
        'countryCode': COUNTRY,
        'langCode': LANGUAGE,
        'loginType': 'EMP',
        'token': access_token,
    }
    return lgedm_post(url, data)


def get_devices(api_root, access_token, session_id):
    """Get a list of devices."""

    url = urljoin(api_root + '/', DEVICE_LIST_PATH)
    return lgedm_post(url, access_token=access_token,
                      session_id=session_id)['item']


class Gateway(object):
    def __init__(self, oauth_base, api_root):
        self.oauth_base = oauth_base
        self.api_root = api_root

    @classmethod
    def discover(cls):
        gw = gateway_info()
        return cls(gw['empUri'], gw['thinqUri'])

    @classmethod
    def load(cls, data):
        return cls(data['oauth_base'], data['api_root'])

    def dump(self):
        return {'oauth_base': self.oauth_base, 'api_root': self.api_root}

    def oauth_url(self):
        return oauth_url(self.oauth_base)


class Auth(object):
    def __init__(self, gateway, access_token):
        self.gateway = gateway
        self.access_token = access_token

    def start_session(self):
        """Start an API session for the logged-in user. Return the
        Session object and the user's devices.
        """

        session_info = login(self.gateway.api_root, self.access_token)
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
        return get_devices(self.auth.gateway.api_root,
                           self.auth.access_token,
                           self.session_id)

    def dump(self):
        return self.session_id

    @classmethod
    def load(cls, auth, data):
        return cls(auth, data)
