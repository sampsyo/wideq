import requests
from urllib.parse import urljoin, urlencode, urlparse, parse_qs
import uuid
import base64
import json
import hashlib
import hmac
import datetime
from collections import namedtuple
import enum


GATEWAY_URL = 'https://kic.lgthinq.com:46030/api/common/gatewayUriList'
APP_KEY = 'wideq'
SECURITY_KEY = 'nuts_securitykey'
DATA_ROOT = 'lgedmRoot'
COUNTRY = 'US'
LANGUAGE = 'en-US'
SVC_CODE = 'SVC202'
CLIENT_ID = 'LGAO221A02'
OAUTH_SECRET_KEY = 'c053c2a6ddeb7ad97cb0eed0dcb31cf8'
OAUTH_CLIENT_KEY = 'LGAO221A02'
DATE_FORMAT = '%a, %d %b %Y %H:%M:%S +0000'


def gen_uuid():
    return str(uuid.uuid4())


def oauth2_signature(message, secret):
    """Get the base64-encoded SHA-1 HMAC digest of a string, as used in
    OAauth2 request signatures.

    Both the `secret` and `message` are given as text strings. We use
    their UTF-8 equivalents.
    """

    secret_bytes = secret.encode('utf8')
    hashed = hmac.new(secret_bytes, message.encode('utf8'), hashlib.sha1)
    digest = hashed.digest()
    return base64.b64encode(digest)


def as_list(obj):
    """Wrap non-lists in lists.

    If `obj` is a list, return it unchanged. Otherwise, return a
    single-element list containing it.
    """

    if isinstance(obj, list):
        return obj
    else:
        return [obj]


class APIError(Exception):
    """An error reported by the API."""

    def __init__(self, code, message):
        self.code = code
        self.message = message


class NotLoggedInError(APIError):
    """The session is not valid or expired."""

    def __init__(self):
        pass


class TokenError(APIError):
    """An authentication token was rejected."""

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


def oauth_url(auth_base):
    """Construct the URL for users to log in (in a browser) to start an
    authenticated session.
    """

    url = urljoin(auth_base, 'login/sign_in')
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
    """Parse the URL to which an OAuth login redirected to obtain two
    tokens: an access token for API credentials, and a refresh token for
    getting updated access tokens.
    """

    params = parse_qs(urlparse(url).query)
    return params['access_token'][0], params['refresh_token'][0]


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


def refresh_auth(oauth_root, refresh_token):
    """Get a new access_token using a refresh_token.

    May raise a `TokenError`.
    """

    token_url = urljoin(oauth_root, '/oauth2/token')
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }

    # The timestamp for labeling OAuth requests can be obtained
    # through a request to the date/time endpoint:
    # https://us.lgeapi.com/datetime
    # But we can also just generate a timestamp.
    timestamp = datetime.datetime.utcnow().strftime(DATE_FORMAT)

    # The signature for the requests is on a string consisting of two
    # parts: (1) a fake request URL containing the refresh token, and (2)
    # the timestamp.
    req_url = ('/oauth2/token?grant_type=refresh_token&refresh_token=' +
               refresh_token)
    sig = oauth2_signature('{}\n{}'.format(req_url, timestamp),
                           OAUTH_SECRET_KEY)

    headers = {
        'lgemp-x-app-key': OAUTH_CLIENT_KEY,
        'lgemp-x-signature': sig,
        'lgemp-x-date': timestamp,
        'Accept': 'application/json',
    }

    res = requests.post(token_url, data=data, headers=headers)
    res_data = res.json()

    if res_data['status'] != 1:
        raise TokenError()
    return res_data['access_token']


class Gateway(object):
    def __init__(self, auth_base, api_root, oauth_root):
        self.auth_base = auth_base
        self.api_root = api_root
        self.oauth_root = oauth_root

    @classmethod
    def discover(cls):
        gw = gateway_info()
        return cls(gw['empUri'], gw['thinqUri'], gw['oauthUri'])

    def oauth_url(self):
        return oauth_url(self.auth_base)


class Auth(object):
    def __init__(self, gateway, access_token, refresh_token):
        self.gateway = gateway
        self.access_token = access_token
        self.refresh_token = refresh_token

    @classmethod
    def from_url(cls, gateway, url):
        """Create an authentication using an OAuth callback URL.
        """

        access_token, refresh_token = parse_oauth_callback(url)
        return cls(gateway, access_token, refresh_token)

    def start_session(self):
        """Start an API session for the logged-in user. Return the
        Session object and a list of the user's devices.
        """

        session_info = login(self.gateway.api_root, self.access_token)
        session_id = session_info['jsessionId']
        return Session(self, session_id), as_list(session_info['item'])

    def refresh(self):
        """Refresh the authentication, returning a new Auth object.
        """

        new_access_token = refresh_auth(self.gateway.oauth_root,
                                        self.refresh_token)
        return Auth(self.gateway, new_access_token, self.refresh_token)


class Session(object):
    def __init__(self, auth, session_id):
        self.auth = auth
        self.session_id = session_id

    def post(self, path, data=None):
        """Make a POST request to the API server.

        This is like `lgedm_post`, but it pulls the context for the
        request from an active Session.
        """

        url = urljoin(self.auth.gateway.api_root + '/', path)
        return lgedm_post(url, data, self.auth.access_token, self.session_id)

    def get_devices(self):
        """Get a list of devices associated with the user's account.

        Return a list of dicts with information about the devices.
        """

        return as_list(self.post('device/deviceList')['item'])

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
            return json.loads(
                base64.b64decode(res['returnData']).decode('utf8')
            )
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

    def set_device_controls(self, device_id, values):
        """Control a device's settings.

        `values` is a key/value map containing the settings to update.
        """

        self.post('rti/rtiControl', {
            'cmd': 'Control',
            'cmdOpt': 'Set',
            'value': values,
            'deviceId': device_id,
            'workId': gen_uuid(),
            'data': '',
        })


class Monitor(object):
    """A monitoring task for a device."""

    def __init__(self, session, device_id):
        self.session = session
        self.device_id = device_id

    def start(self):
        self.work_id = self.session.monitor_start(self.device_id)

    def stop(self):
        self.session.monitor_stop(self.device_id, self.work_id)

    def poll(self):
        return self.session.monitor_poll(self.device_id, self.work_id)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, tb):
        self.stop()


class Client(object):
    """A higher-level API wrapper that provides a session more easily
    and allows serialization of state.
    """

    def __init__(self, gateway=None, auth=None, session=None):
        # The three steps required to get access to call the API.
        self._gateway = gateway
        self._auth = auth
        self._session = session

        # The last list of devices we got from the server. This is the
        # raw JSON list data describing the devices.
        self._devices = None

        # Cached model info data. This is a mapping from URLs to JSON
        # responses.
        self._model_info = {}

    @property
    def gateway(self):
        if not self._gateway:
            self._gateway = Gateway.discover()
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
        """DeviceInfo objects describing the user's devices.
        """

        if not self._devices:
            self._devices = self.session.get_devices()
        return (DeviceInfo(d) for d in self._devices)

    def get_device(self, device_id):
        """Look up a DeviceInfo object by device ID.

        Return None if the device does not exist.
        """

        for device in self.devices:
            if device.id == device_id:
                return device
        return None

    @classmethod
    def load(cls, state):
        """Load a client from serialized state.
        """

        client = cls()

        if 'gateway' in state:
            data = state['gateway']
            client._gateway = Gateway(
                data['auth_base'], data['api_root'], data['oauth_root']
            )

        if 'auth' in state:
            data = state['auth']
            client._auth = Auth(
                client.gateway, data['access_token'], data['refresh_token']
            )

        if 'session' in state:
            client._session = Session(client.auth, state['session'])

        if 'model_info' in state:
            client._model_info = state['model_info']

        return client

    def dump(self):
        """Serialize the client state."""

        out = {
            'model_info': self._model_info,
        }

        if self._gateway:
            out['gateway'] = {
                'auth_base': self._gateway.auth_base,
                'api_root': self._gateway.api_root,
                'oauth_root': self._gateway.oauth_root,
            }

        if self._auth:
            out['auth'] = {
                'access_token': self._auth.access_token,
                'refresh_token': self._auth.refresh_token,
            }

        if self._session:
            out['session'] = self._session.session_id

        return out

    def refresh(self):
        self._auth = self.auth.refresh()
        self._session, self._devices = self.auth.start_session()

    @classmethod
    def from_token(cls, refresh_token):
        """Construct a client using just a refresh token.

        This allows simpler state storage (e.g., for human-written
        configuration) but it is a little less efficient because we need
        to reload the gateway servers and restart the session.
        """

        client = cls()
        client._auth = Auth(client.gateway, None, refresh_token)
        client.refresh()
        return client

    def model_info(self, device):
        """For a DeviceInfo object, get a ModelInfo object describing
        the model's capabilities.
        """
        url = device.model_info_url
        if url not in self._model_info:
            self._model_info[url] = device.load_model_info()
        return ModelInfo(self._model_info[url])


class DeviceInfo(object):
    """Details about a user's device.

    This is populated from a JSON dictionary provided by the API.
    """

    def __init__(self, data):
        self.data = data

    @property
    def model_id(self):
        return self.data['modelNm']

    @property
    def id(self):
        return self.data['deviceId']

    @property
    def model_info_url(self):
        return self.data['modelJsonUrl']

    @property
    def name(self):
        return self.data['alias']

    def load_model_info(self):
        """Load JSON data describing the model's capabilities.
        """
        return requests.get(self.model_info_url).json()


EnumValue = namedtuple('EnumValue', ['options'])
RangeValue = namedtuple('RangeValue', ['min', 'max', 'step'])


class ModelInfo(object):
    """A description of a device model's capabilities.
    """

    def __init__(self, data):
        self.data = data

    def value(self, name):
        """Look up information about a value.

        Return either an `EnumValue` or a `RangeValue`.
        """
        d = self.data['Value'][name]
        if d['type'] in ('Enum', 'enum'):
            return EnumValue(d['option'])
        elif d['type'] == 'Range':
            return RangeValue(
                d['option']['min'], d['option']['max'], d['option']['step']
            )
        else:
            assert False, "unsupported value type {}".format(d['type'])

    def default(self, name):
        """Get the default value, if it exists, for a given value.
        """

        return self.data['Value'][name]['default']

    def enum_value(self, key, name):
        """Look up the encoded value for a friendly enum name.
        """

        options = self.value(key).options
        options_inv = {v: k for k, v in options.items()}  # Invert the map.
        return options_inv[name]

    def enum_name(self, key, value):
        """Look up the friendly enum name for an encoded value.
        """

        options = self.value(key).options
        return options[value]


class ACMode(enum.Enum):
    """The operation mode for an AC/HVAC device."""

    COOL = "@AC_MAIN_OPERATION_MODE_COOL_W"
    DRY = "@AC_MAIN_OPERATION_MODE_DRY_W"
    FAN = "@AC_MAIN_OPERATION_MODE_FAN_W"
    AI = "@AC_MAIN_OPERATION_MODE_AI_W"
    HEAT = "@AC_MAIN_OPERATION_MODE_HEAT_W"
    AIRCLEAN = "@AC_MAIN_OPERATION_MODE_AIRCLEAN_W"
    ACO = "@AC_MAIN_OPERATION_MODE_ACO_W"
    AROMA = "@AC_MAIN_OPERATION_MODE_AROMA_W"
    ENERGY_SAVING = "@AC_MAIN_OPERATION_MODE_ENERGY_SAVING_W"


class ACOp(enum.Enum):
    """Whether a device is on or off."""

    OFF = "@AC_MAIN_OPERATION_OFF_W"
    RIGHT_ON = "@AC_MAIN_OPERATION_RIGHT_ON_W"  # This one seems to mean "on"?
    LEFT_ON = "@AC_MAIN_OPERATION_LEFT_ON_W"
    ALL_ON = "@AC_MAIN_OPERATION_ALL_ON_W"


class ACDevice(object):
    """Higher-level operations on an AC/HVAC device, such as a heat
    pump.
    """

    def __init__(self, client, device):
        """Create a wrapper for a `DeviceInfo` object associated with a
        `Client`.
        """

        self.client = client
        self.device = device
        self.model = client.model_info(device)

    @property
    def f2c(self):
        """Get a dictionary mapping Fahrenheit to Celsius temperatures for
        this device.

        Unbelievably, SmartThinQ devices have their own lookup tables
        for mapping the two temperature scales. You can get *close* by
        using a real conversion between the two temperature scales, but
        precise control requires using the custom LUT.
        """

        mapping = self.model.value('TempFahToCel').options
        return {int(f): c for f, c in mapping.items()}

    @property
    def c2f(self):
        """Get an inverse mapping from Celsius to Fahrenheit.
        """

        return {v: k for k, v in self.f2c.items()}

    def _set_control(self, key, value):
        """Set a device's control for `key` to `value`.
        """

        self.client.session.set_device_controls(
            self.device.id,
            {key: value},
        )

    def set_celsius(self, c):
        """Set the device's target temperature in Celsius degrees.
        """

        self._set_control('TempCfg', c)

    def set_fahrenheit(self, f):
        """Set the device's target temperature in Fahrenheit degrees.
        """

        self.set_celsius(self.f2c[f])

    def set_mode(self, mode):
        """Set the device's operating mode to an `OpMode` value.
        """

        mode_value = self.model.enum_value('OpMode', mode.value)
        self._set_control('OpMode', mode_value)

    def set_on(self, is_on):
        """Turn on or off the device (according to a boolean).
        """

        op = ACOp.RIGHT_ON if is_on else ACOp.OFF
        op_value = self.model.enum_value('Operation', op.value)
        self._set_control('Operation', op_value)

    def monitor_start(self):
        """Start monitoring the device's status."""

        self.mon = Monitor(self.client.session, self.device.id)
        self.mon.start()

    def monitor_stop(self):
        """Stop monitoring the device's status."""

        self.mon.stop()

    def poll(self):
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`. Return
        either an `ACStatus` object or `None` if the status is not yet
        available.
        """

        res = self.mon.poll()
        if res:
            return ACStatus(self, res)
        else:
            return None


class ACStatus(object):
    """Higher-level information about an AC device's current status.
    """

    def __init__(self, ac, data):
        self.ac = ac
        self.data = data

    @staticmethod
    def _str_to_num(s):
        """Convert a string to either an `int` or a `float`.

        Troublingly, the API likes values like "18", without a trailing
        ".0", for whole numbers. So we use `int`s for integers and
        `float`s for non-whole numbers.
        """

        f = float(s)
        if f == int(f):
            return int(f)
        else:
            return f

    @property
    def temp_cur_c(self):
        return self._str_to_num(self.data['TempCur'])

    @property
    def temp_cur_f(self):
        return self.ac.c2f[self.temp_cur_c]

    @property
    def temp_cfg_c(self):
        return self._str_to_num(self.data['TempCfg'])

    @property
    def temp_cfg_f(self):
        return self.ac.c2f[self.temp_cfg_c]

    def lookup_enum(self, key):
        return self.ac.model.enum_name(key, self.data[key])

    @property
    def mode(self):
        return ACMode(self.lookup_enum('OpMode'))

    @property
    def is_on(self):
        op = ACOp(self.lookup_enum('Operation'))
        return op != ACOp.OFF
