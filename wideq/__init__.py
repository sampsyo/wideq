"""Reverse-engineered client for the LG SmartThinQ API.
"""
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

__version__ = '1.0.1'

GATEWAY_URL = 'https://kic.lgthinq.com:46030/api/common/gatewayUriList'
APP_KEY = 'wideq'
SECURITY_KEY = 'nuts_securitykey'
DATA_ROOT = 'lgedmRoot'
DEFAULT_COUNTRY = 'US'
DEFAULT_LANGUAGE = 'en-US'
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


def get_list(obj, key):
    """Look up a list using a key from an object.

    If `obj[key]` is a list, return it unchanged. If is something else,
    return a single-element list containing it. If the key does not
    exist, return an empty list.
    """

    try:
        val = obj[key]
    except KeyError:
        return []

    if isinstance(val, list):
        return val
    else:
        return [val]


class APIError(Exception):
    """An error reported by the API."""

    def __init__(self, code, message):
        self.code = code
        self.message = message


class NotLoggedInError(APIError):
    """The session is not valid or expired."""

    def __init__(self):
        pass


class NotConnectedError(APIError):
    """The service can't contact the specified device."""

    def __init__(self):
        pass


class TokenError(APIError):
    """An authentication token was rejected."""

    def __init__(self):
        pass


class MonitorError(APIError):
    """Monitoring a device failed, possibly because the monitoring
    session failed and needs to be restarted.
    """

    def __init__(self, device_id, code):
        self.device_id = device_id
        self.code = code


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
            elif code == "0106":
                raise NotConnectedError()
            else:
                raise APIError(code, message)

    return out


def gateway_info(country, language):
    """Load information about the hosts to use for API interaction.

    `country` and `language` are codes, like "US" and "en-US,"
    respectively.
    """

    return lgedm_post(
        GATEWAY_URL,
        {'countryCode': country, 'langCode': language},
    )


def oauth_url(auth_base, country, language):
    """Construct the URL for users to log in (in a browser) to start an
    authenticated session.
    """

    url = urljoin(auth_base, 'login/sign_in')
    query = urlencode({
        'country': country,
        'language': language,
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


def login(api_root, access_token, country, language):
    """Use an access token to log into the API and obtain a session and
    return information about the session.
    """

    url = urljoin(api_root + '/', 'member/login')
    data = {
        'countryCode': country,
        'langCode': language,
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
    def __init__(self, auth_base, api_root, oauth_root, country, language):
        self.auth_base = auth_base
        self.api_root = api_root
        self.oauth_root = oauth_root
        self.country = country
        self.language = language

    @classmethod
    def discover(cls, country, language):
        gw = gateway_info(country, language)
        return cls(gw['empUri'], gw['thinqUri'], gw['oauthUri'],
                   country, language)

    def oauth_url(self):
        return oauth_url(self.auth_base, self.country, self.language)


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

        session_info = login(self.gateway.api_root, self.access_token,
                             self.gateway.country, self.gateway.language)
        session_id = session_info['jsessionId']
        return Session(self, session_id), get_list(session_info, 'item')

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

        return get_list(self.post('device/deviceList'), 'item')

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

        `work_id` is a string ID retrieved from `monitor_start`. Return
        a status result, which is a bytestring, or None if the
        monitoring is not yet ready.

        May raise a `MonitorError`, in which case the right course of
        action is probably to restart the monitoring task.
        """

        work_list = [{'deviceId': device_id, 'workId': work_id}]
        res = self.post('rti/rtiResult', {'workList': work_list})['workList']

        # Check for errors.
        code = res.get('returnCode')  # returnCode can be missing.
        if code != '0000':
            raise MonitorError(device_id, code)

        # The return data may or may not be present, depending on the
        # monitoring task status.
        if 'returnData' in res:
            # The main response payload is base64-encoded binary data in
            # the `returnData` field. This sometimes contains JSON data
            # and sometimes other binary data.
            return base64.b64decode(res['returnData'])
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

        return self.post('rti/rtiControl', {
            'cmd': 'Control',
            'cmdOpt': 'Set',
            'value': values,
            'deviceId': device_id,
            'workId': gen_uuid(),
            'data': '',
        })

    def get_device_config(self, device_id, key, category='Config'):
        """Get a device configuration option.

        The `category` string should probably either be "Config" or
        "Control"; the right choice appears to depend on the key.
        """

        res = self.post('rti/rtiControl', {
            'cmd': category,
            'cmdOpt': 'Get',
            'value': key,
            'deviceId': device_id,
            'workId': gen_uuid(),
            'data': '',
        })
        return res['returnData']


class Monitor(object):
    """A monitoring task for a device.

    This task is robust to some API-level failures. If the monitoring
    task expires, it attempts to start a new one automatically. This
    makes one `Monitor` object suitable for long-term monitoring.
    """

    def __init__(self, session, device_id):
        self.session = session
        self.device_id = device_id

    def start(self):
        self.work_id = self.session.monitor_start(self.device_id)

    def stop(self):
        self.session.monitor_stop(self.device_id, self.work_id)

    def poll(self):
        """Get the current status data (a bytestring) or None if the
        device is not yet ready.
        """

        try:
            return self.session.monitor_poll(self.device_id, self.work_id)
        except MonitorError:
            # Try to restart the task.
            self.stop()
            self.start()
            return None

    @staticmethod
    def decode_json(data):
        """Decode a bytestring that encodes JSON status data."""

        return json.loads(data.decode('utf8'))

    def poll_json(self):
        """For devices where status is reported via JSON data, get the
        decoded status result (or None if status is not available).
        """

        data = self.poll()
        return self.decode_json(data) if data else None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, tb):
        self.stop()


class Client(object):
    """A higher-level API wrapper that provides a session more easily
    and allows serialization of state.
    """

    def __init__(self, gateway=None, auth=None, session=None,
                 country=DEFAULT_COUNTRY, language=DEFAULT_LANGUAGE):
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

        # Locale information used to discover a gateway, if necessary.
        self._country = country
        self._language = language

    @property
    def gateway(self):
        if not self._gateway:
            self._gateway = Gateway.discover(self._country, self._language)
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
                data['auth_base'], data['api_root'], data['oauth_root'],
                data.get('country', DEFAULT_COUNTRY),
                data.get('language', DEFAULT_LANGUAGE),
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

        if 'country' in state:
            client._country = state['country']

        if 'language' in state:
            client._language = state['language']

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
                'country': self._gateway.country,
                'language': self._gateway.language,
            }

        if self._auth:
            out['auth'] = {
                'access_token': self._auth.access_token,
                'refresh_token': self._auth.refresh_token,
            }

        if self._session:
            out['session'] = self._session.session_id

        out['country'] = self._country
        out['language'] = self._language

        return out

    def refresh(self):
        self._auth = self.auth.refresh()
        self._session, self._devices = self.auth.start_session()

    @classmethod
    def from_token(cls, refresh_token, country=None, language=None):
        """Construct a client using just a refresh token.

        This allows simpler state storage (e.g., for human-written
        configuration) but it is a little less efficient because we need
        to reload the gateway servers and restart the session.
        """

        client = cls(
            country=country or DEFAULT_COUNTRY,
            language=language or DEFAULT_LANGUAGE,
        )
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


class DeviceType(enum.Enum):
    """The category of device."""

    REFRIGERATOR = 101
    KIMCHI_REFRIGERATOR = 102
    WATER_PURIFIER = 103
    WASHER = 201
    DRYER = 202
    STYLER = 203
    DISHWASHER = 204
    OVEN = 301
    MICROWAVE = 302
    COOKTOP = 303
    HOOD = 304
    AC = 401  # Includes heat pumps, etc., possibly all HVAC devices.
    AIR_PURIFIER = 402
    DEHUMIDIFIER = 403
    ROBOT_KING = 501  # Robotic vacuum cleaner?
    ARCH = 1001
    MISSG = 3001
    SENSOR = 3002
    SOLAR_SENSOR = 3102
    IOT_LIGHTING = 3003
    IOT_MOTION_SENSOR = 3004
    IOT_SMART_PLUG = 3005
    IOT_DUST_SENSOR = 3006
    EMS_AIR_STATION = 4001
    AIR_SENSOR = 4003


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

    @property
    def type(self):
        """The kind of device, as a `DeviceType` value."""

        return DeviceType(self.data['deviceType'])

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

    @property
    def binary_monitor_data(self):
        """Check that type of monitoring is BINARY(BYTE).
        """

        return self.data['Monitoring']['type'] == 'BINARY(BYTE)'

    def decode_monitor_binary(self, data):
        """Decode binary encoded status data.
        """

        decoded = {}
        for item in self.data['Monitoring']['protocol']:
            key = item['value']
            value = 0
            for v in data[item['startByte']:item['startByte'] +
                          item['length']]:
                value = (value << 8) + v
            decoded[key] = str(value)
        return decoded

    def decode_monitor_json(self, data):
        """Decode a bytestring that encodes JSON status data."""

        return json.loads(data.decode('utf8'))

    def decode_monitor(self, data):
        """Decode  status data."""

        if self.binary_monitor_data:
            return self.decode_monitor_binary(data)
        else:
            return self.decode_monitor_json(data)


class Device(object):
    """A higher-level interface to a specific device.

    Unlike `DeviceInfo`, which just stores data *about* a device,
    `Device` objects refer to their client and can perform operations
    regarding the device.
    """

    def __init__(self, client, device):
        """Create a wrapper for a `DeviceInfo` object associated with a
        `Client`.
        """

        self.client = client
        self.device = device
        self.model = client.model_info(device)

    def _set_control(self, key, value):
        """Set a device's control for `key` to `value`.
        """

        self.client.session.set_device_controls(
            self.device.id,
            {key: value},
        )

    def _get_config(self, key):
        """Look up a device's configuration for a given value.

        The response is parsed as base64-encoded JSON.
        """

        data = self.client.session.get_device_config(
            self.device.id,
            key,
        )
        return json.loads(base64.b64decode(data).decode('utf8'))

    def _get_control(self, key):
        """Look up a device's control value.
        """

        data = self.client.session.get_device_config(
            self.device.id,
            key,
            'Control',
        )

        # The response comes in a funky key/value format: "(key:value)".
        _, value = data[1:-1].split(':')
        return value


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


class ACFanSpeed(enum.Enum):
    """The fan speed for an AC/HVAC device."""

    SLOW = '@AC_MAIN_WIND_STRENGTH_SLOW_W'
    SLOW_LOW = '@AC_MAIN_WIND_STRENGTH_SLOW_LOW_W'
    LOW = '@AC_MAIN_WIND_STRENGTH_LOW_W'
    LOW_MID = '@AC_MAIN_WIND_STRENGTH_LOW_MID_W'
    MID = '@AC_MAIN_WIND_STRENGTH_MID_W'
    MID_HIGH = '@AC_MAIN_WIND_STRENGTH_MID_HIGH_W'
    HIGH = '@AC_MAIN_WIND_STRENGTH_HIGH_W'
    POWER = '@AC_MAIN_WIND_STRENGTH_POWER_W'
    AUTO = '@AC_MAIN_WIND_STRENGTH_AUTO_W'


class ACOp(enum.Enum):
    """Whether a device is on or off."""

    OFF = "@AC_MAIN_OPERATION_OFF_W"
    RIGHT_ON = "@AC_MAIN_OPERATION_RIGHT_ON_W"  # This one seems to mean "on"?
    LEFT_ON = "@AC_MAIN_OPERATION_LEFT_ON_W"
    ALL_ON = "@AC_MAIN_OPERATION_ALL_ON_W"


class ACDevice(Device):
    """Higher-level operations on an AC/HVAC device, such as a heat
    pump.
    """

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

        Just as unbelievably, this is not exactly the inverse of the
        `f2c` map. There are a few values in this reverse mapping that
        are not in the other.
        """

        mapping = self.model.value('TempCelToFah').options
        out = {}
        for c, f in mapping.items():
            try:
                c_num = int(c)
            except ValueError:
                c_num = float(c)
            out[c_num] = f
        return out

    def set_celsius(self, c):
        """Set the device's target temperature in Celsius degrees.
        """

        self._set_control('TempCfg', c)

    def set_fahrenheit(self, f):
        """Set the device's target temperature in Fahrenheit degrees.
        """

        self.set_celsius(self.f2c[f])

    def set_zones(self, zones):
        """Turn off or on the device's zones.

        The `zones` parameter is a list of dicts with these keys:
        - "No": The zone index. A string containing a number,
          starting from 1.
        - "Cfg": Whether the zone is enabled. A string, either "1" or
          "0".
        - "State": Whether the zone is open. Also "1" or "0".
        """

        # Ensure at least one zone is enabled: we can't turn all zones
        # off simultaneously.
        on_count = sum(int(zone['State']) for zone in zones)
        if on_count > 0:
            zone_cmd = '/'.join(
                '{}_{}'.format(zone['No'], zone['State'])
                for zone in zones if zone['Cfg'] == '1'
            )
            self._set_control('DuctZone', zone_cmd)

    def get_zones(self):
        """Get the status of the zones, including whether a zone is
        configured.

        The result is a list of dicts with the same format as described in
        `set_zones`.
        """

        return self._get_config('DuctZone')

    def set_fan_speed(self, speed):
        """Set the fan speed to a value from the `ACFanSpeed` enum.
        """

        speed_value = self.model.enum_value('WindStrength', speed.value)
        self._set_control('WindStrength', speed_value)

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

    def get_filter_state(self):
        """Get information about the filter."""

        return self._get_config('Filter')

    def get_mfilter_state(self):
        """Get information about the "MFilter" (not sure what this is).
        """

        return self._get_config('MFilter')

    def get_energy_target(self):
        """Get the configured energy target data."""

        return self._get_config('EnergyDesiredValue')

    def get_light(self):
        """Get a Boolean indicating whether the display light is on."""

        value = self._get_control('DisplayControl')
        return value == '0'  # Seems backwards, but isn't.

    def get_volume(self):
        """Get the speaker volume level."""

        value = self._get_control('SpkVolume')
        return int(value)

    def monitor_start(self):
        """Start monitoring the device's status."""

        mon = Monitor(self.client.session, self.device.id)
        mon.start()
        self.mon = mon

    def monitor_stop(self):
        """Stop monitoring the device's status."""

        self.mon.stop()

    def poll(self):
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`. Return
        either an `ACStatus` object or `None` if the status is not yet
        available.
        """

        # Abort if monitoring has not started yet.
        if not hasattr(self, 'mon'):
            return None

        res = self.mon.poll_json()
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
    def fan_speed(self):
        return ACFanSpeed(self.lookup_enum('WindStrength'))

    @property
    def is_on(self):
        op = ACOp(self.lookup_enum('Operation'))
        return op != ACOp.OFF
