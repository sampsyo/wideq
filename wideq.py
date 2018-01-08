import requests
from urllib.parse import urljoin, urlencode, urlparse, parse_qs
import uuid
import base64
import json


GATEWAY_URL = 'https://kic.lgthinq.com:46030/api/common/gatewayUriList'
APP_KEY = 'wideq'
SECURITY_KEY = 'nuts_securitykey'
DATA_ROOT = 'lgedmRoot'
COUNTRY = 'US'
LANGUAGE = 'en-US'
SVC_CODE = 'SVC202'
CLIENT_ID = 'LGAO221A02'


def gen_uuid():
    return str(uuid.uuid4())


class APIError(Exception):
    """An error reported by the API."""

    def __init__(self, code, message):
        self.code = code
        self.message = message


class NotLoggedInError(APIError):
    """The session is not valid or expired."""

    def __init__(self):
        pass


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
    out = res.json()[DATA_ROOT]

    # Check for API errors.
    if 'returnCd' in out:
        code = out['returnCd']
        if code != '0000':
            message = out['returnMsg']
            if code == "0102":
                raise NotLoggedInError()
            else:
                raise APIError(code, message)

    return out


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

    url = urljoin(oauth_base, 'login/sign_in')
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

    url = urljoin(api_root + '/', 'member/login')
    data = {
        'countryCode': COUNTRY,
        'langCode': LANGUAGE,
        'loginType': 'EMP',
        'token': access_token,
    }
    return lgedm_post(url, data)


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

    def dump(self):
        return self.session_id

    @classmethod
    def load(cls, auth, data):
        return cls(auth, data)

    def post(self, path, data=None):
        """Make a POST request to the API server.

        This is like `lgedm_post`, but it pulls the context for the
        request from an active Session.
        """
        url = urljoin(self.auth.gateway.api_root + '/', path)
        return lgedm_post(url, data, self.auth.access_token, self.session_id)

    def get_devices(self):
        return self.post('device/deviceList')['item']

    def monitor_start(self, device_id):
        """Begin monitoring a device's status.

        Return a "work ID" that can be used to retrieve the result of
        monitoring.
        """

        res = self.post('rti/rtiMon', {
            'cmd': 'Mon',
            'cmdOpt': 'Start',
            'deviceId': device_id,
            'workId': gen_uuid(),
        })
        return res['workId']

    def monitor_poll(self, device_id, work_id):
        """Get the result of a monitoring task.

        `work_ids` is a mapping from device IDs to work IDs. Return the
        device status or None if the monitoring is not yet ready.
        """

        work_list = [{'deviceId': device_id, 'workId': work_id}]
        res = self.post('rti/rtiResult', {'workList': work_list})['workList']

        # Weirdly, the main response data is base64-encoded JSON.
        if 'returnData' in res:
            return json.loads(base64.b64decode(res['returnData']))
        else:
            return None

    def monitor_stop(self, device_id, work_id):
        """Stop monitoring a device."""

        self.post('rti/rtiMon', {
            'cmd': 'Mon',
            'cmdOpt': 'Stop',
            'deviceId': device_id,
            'workId': work_id,
        })

    def set_device_control(self, device_id, key, value):
        """Control a device's settings."""

        res = self.post('rti/rtiControl', {
            'cmd': 'Control',
            'cmdOpt': key,
            'value': value,
            'deviceId': device_id,
            'workId': gen_uuid(),
            'data': '',
        })
        print(res)


class Monitor(object):
    """A monitoring task for a device."""

    def __init__(self, session, device_id):
        self.session = session
        self.device_id = device_id

    def __enter__(self):
        self.work_id = self.session.monitor_start(self.device_id)
        return self

    def poll(self):
        return self.session.monitor_poll(self.device_id, self.work_id)

    def __exit__(self, type, value, tb):
        self.session.monitor_stop(self.device_id, self.work_id)
