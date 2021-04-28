"""A low-level, general abstraction for the LG SmartThinQ API.
"""
import base64
from enum import Enum
import uuid
from urllib.parse import urljoin, urlencode, urlparse, parse_qs
import hashlib
import hmac
import datetime
import requests
import logging
from typing import Any, Dict, List, Tuple
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

GATEWAY_URL = (
    "https://route.lgthinq.com:46030/v1/service/application/gateway-uri"
)
SECURITY_KEY = "nuts_securitykey"
APP_KEY = "wideq"
DATA_ROOT = "result"
POST_DATA_ROOT = "lgedmRoot"
RETURN_CODE_ROOT = "resultCode"
RETURN_MESSAGE_ROOT = "returnMsg"
SVC_CODE = "SVC202"
OAUTH_SECRET_KEY = "c053c2a6ddeb7ad97cb0eed0dcb31cf8"
OAUTH_CLIENT_KEY = "LGAO221A02"
DATE_FORMAT = "%a, %d %b %Y %H:%M:%S +0000"
DEFAULT_COUNTRY = "US"
DEFAULT_LANGUAGE = "en-US"

# v2
API_KEY = "VGhpblEyLjAgU0VSVklDRQ=="

# the client id is a SHA512 hash of the phone MFR,MODEL,SERIAL,
# and the build id of the thinq app it can also just be a random
# string, we use the same client id used for oauth
CLIENT_ID = OAUTH_CLIENT_KEY
MESSAGE_ID = "wideq"
SVC_PHASE = "OP"
APP_LEVEL = "PRD"
APP_OS = "ANDROID"
APP_TYPE = "NUTS"
APP_VER = "3.5.1200"


OAUTH_REDIRECT_URI = "https://kr.m.lgaccount.com/login/iabClose"

RETRY_COUNT = 5  # Anecdotally this seems sufficient.
RETRY_FACTOR = 0.5
RETRY_STATUSES = (502, 503, 504)


def get_wideq_logger() -> logging.Logger:
    level = logging.INFO
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logger = logging.getLogger("wideq")
    logger.setLevel(level)

    try:
        import colorlog  # type: ignore

        colorfmt = f"%(log_color)s{fmt}%(reset)s"
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter(
                colorfmt,
                datefmt=datefmt,
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red",
                },
            )
        )
    except ImportError:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    logger.addHandler(handler)
    return logger


LOGGER = get_wideq_logger()


def retry_session():
    """Get a Requests session that retries HTTP and HTTPS requests."""
    # Adapted from:
    # https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    session = requests.Session()
    retry = Retry(
        total=RETRY_COUNT,
        read=RETRY_COUNT,
        connect=RETRY_COUNT,
        backoff_factor=RETRY_FACTOR,
        status_forcelist=RETRY_STATUSES,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def set_log_level(level: int):
    logger = get_wideq_logger()
    logger.setLevel(level)


def gen_uuid() -> str:
    return str(uuid.uuid4())


def oauth2_signature(message: str, secret: str) -> bytes:
    """Get the base64-encoded SHA-1 HMAC digest of a string, as used in
    OAauth2 request signatures.

    Both the `secret` and `message` are given as text strings. We use
    their UTF-8 equivalents.
    """

    secret_bytes = secret.encode("utf8")
    hashed = hmac.new(secret_bytes, message.encode("utf8"), hashlib.sha1)
    digest = hashed.digest()
    return base64.b64encode(digest)


def get_list(obj, key: str) -> List[Dict[str, Any]]:
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

    def __init__(self, code, message=None):
        self.code = code
        self.message = message


class NotLoggedInError(APIError):
    """The session is not valid or expired."""


class NotConnectedError(APIError):
    """The service can't contact the specified device."""


class TokenError(APIError):
    """An authentication token was rejected."""

    def __init__(self):
        pass


class FailedRequestError(APIError):
    """A failed request typically indicates an unsupported control on a
    device.
    """


class InvalidCredentialError(APIError):
    """The server rejected connection."""

    def __init__(self):
        pass


class InvalidRequestError(APIError):
    """The server rejected a request as invalid."""


class DeviceNotFoundError:
    """The device couldn't be found."""


class MonitorError(APIError):
    """Monitoring a device failed, possibly because the monitoring
    session failed and needs to be restarted.
    """

    def __init__(self, device_id, code):
        self.device_id = device_id
        self.code = code


class MalformedResponseError(APIError):
    """The server produced malformed data, such as invalid JSON."""

    def __init__(self, data):
        self.data = data


API_ERRORS = {
    "0102": NotLoggedInError,
    "0106": NotConnectedError,
    "0100": FailedRequestError,
    "0110": InvalidCredentialError,
    9000: InvalidRequestError,  # Surprisingly, an integer (not a string).
    9003: NotLoggedInError,  # Session Creation FailureError
}


class RequestMethod(Enum):
    GET = "get"
    POST = "post"


def thinq_request(
    method,
    url,
    data=None,
    access_token=None,
    session_id=None,
    user_number=None,
    country=DEFAULT_COUNTRY,
    language=DEFAULT_LANGUAGE,
):
    """Make an HTTP request in the format used by the API servers.

    In this format, the request POST data sent as JSON under a special
    key; authentication sent in headers. Return the JSON data extracted
    from the response.

    The `access_token` and `session_id` are required for most normal,
    authenticated requests. They are not required, for example, to load
    the gateway server data or to start a session.
    """
    headers = {
        "Accept": "application/json",
        "x-api-key": API_KEY,
        "x-client-id": CLIENT_ID,
        "x-country-code": country,
        "x-language-code": language,
        "x-message-id": MESSAGE_ID,
        "x-service-code": SVC_CODE,
        "x-service-phase": SVC_PHASE,
        "x-thinq-app-level": APP_LEVEL,
        "x-thinq-app-os": APP_OS,
        "x-thinq-app-type": APP_TYPE,
        "x-thinq-app-ver": APP_VER,
    }

    if access_token:
        headers["x-emp-token"] = access_token
    if user_number:
        headers["x-user-no"] = user_number

    with retry_session() as session:
        if method == RequestMethod.POST:
            res = session.post(url, json=data, headers=headers)
        elif method == RequestMethod.GET:
            res = session.get(url, headers=headers)
        else:
            raise ValueError("Unsupported request method")

    out = res.json()

    # Check for API errors.
    if RETURN_CODE_ROOT in out:
        code = out[RETURN_CODE_ROOT]
        if code != "0000":
            if code in API_ERRORS:
                raise API_ERRORS[code](code)
            else:
                raise APIError(code)

    return out[DATA_ROOT]


def oauth_url(auth_base, country, language):
    """Construct the URL for users to log in (in a browser) to start an
    authenticated session.
    """

    url = urljoin(auth_base, "spx/login/signIn")
    query = urlencode(
        {
            "country": country,
            "language": language,
            "svc_list": SVC_CODE,
            "client_id": CLIENT_ID,
            "division": "ha",
            "redirect_uri": OAUTH_REDIRECT_URI,
            "state": uuid.uuid1().hex,
            "show_thirdparty_login": "AMZ,FBK",
        }
    )

    return "{}?{}".format(url, query)


def parse_oauth_callback(url):
    """Parse the URL to which an OAuth login redirected to obtain two
    tokens: an access token for API credentials, and a refresh token for
    getting updated access tokens.
    """

    params = parse_qs(urlparse(url).query)
    return (
        params["oauth2_backend_url"][0],
        params["code"][0],
        params["user_number"][0],
    )


class OAuthGrant(Enum):
    REFRESH_TOKEN = "refresh_token"
    AUTHORIZATION_CODE = "authorization_code"


def oauth_request(grant, oauth_root, token):
    """Make an oauth_request with a specific grant type

    May raise a `TokenError`.
    """

    oauth_path = "/oauth/1.0/oauth2/token"
    token_url = urljoin(oauth_root, oauth_path)
    data = {}

    if grant == OAuthGrant.REFRESH_TOKEN:
        data["grant_type"] = "refresh_token"
        data["refresh_token"] = token
    elif grant == OAuthGrant.AUTHORIZATION_CODE:
        data["code"] = token
        data["grant_type"] = "authorization_code"
        data["redirect_uri"] = OAUTH_REDIRECT_URI
    else:
        raise ValueError("Unsupported grant")

    # The timestamp for labeling OAuth requests can be obtained
    # through a request to the date/time endpoint:
    # https://us.lgeapi.com/datetime
    # But we can also just generate a timestamp.
    timestamp = datetime.datetime.utcnow().strftime(DATE_FORMAT)

    # The signature for the requests is on a string consisting of two
    # parts: (1) a fake request URL containing the refresh token, and (2)
    # the timestamp.
    req_url = "{}?{}".format(oauth_path, urlencode(data))
    sig = oauth2_signature(
        "{}\n{}".format(req_url, timestamp), OAUTH_SECRET_KEY
    )

    headers = {
        "x-lge-appkey": CLIENT_ID,
        "x-lge-oauth-signature": sig,
        "x-lge-oauth-date": timestamp,
        "Accept": "application/json",
    }

    with retry_session() as session:
        res = session.post(token_url, data=data, headers=headers)
    res_data = res.json()

    if res.status_code != 200:
        raise TokenError()

    return res_data


class Gateway(object):
    def __init__(self, auth_base, api_root, country, language):
        self.auth_base = auth_base
        self.api_root = api_root
        self.country = country
        self.language = language

    @classmethod
    def discover(cls, country, language) -> "Gateway":
        """Load information about the hosts to use for API interaction.

        `country` and `language` are codes, like "US" and "en-US,"
        respectively.
        """
        gw = thinq_request(
            RequestMethod.GET,
            GATEWAY_URL,
            {"countryCode": country, "langCode": language},
            country=country,
            language=language,
        )
        return cls(gw["empUri"], gw["thinq2Uri"], country, language)

    def oauth_url(self):
        return oauth_url(self.auth_base, self.country, self.language)

    def serialize(self) -> Dict[str, str]:
        return {
            "auth_base": self.auth_base,
            "api_root": self.api_root,
            "country": self.country,
            "language": self.language,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "Gateway":
        return cls(
            data["auth_base"],
            data["api_root"],
            data.get("country", DEFAULT_COUNTRY),
            data.get("language", DEFAULT_LANGUAGE),
        )


class Auth(object):
    def __init__(
        self, gateway, access_token, refresh_token, user_number, oauth_root
    ):
        self.gateway = gateway
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_number = user_number
        self.oauth_root = oauth_root

    @classmethod
    def from_url(cls, gateway, url):
        """Create an authentication using an OAuth callback URL."""

        oauth_root, auth_code, user_number = parse_oauth_callback(url)
        out = oauth_request(
            OAuthGrant.AUTHORIZATION_CODE, oauth_root, auth_code
        )
        return cls(
            gateway,
            out["access_token"],
            out["refresh_token"],
            user_number,
            oauth_root,
        )

    def start_session(self) -> Tuple["Session", List[Dict[str, Any]]]:
        """Start an API session for the logged-in user. Return the
        Session object and a list of the user's devices.
        """
        return Session(self), []

    def refresh(self):
        """Refresh the authentication, returning a new Auth object."""

        new_access_token = oauth_request(
            OAuthGrant.REFRESH_TOKEN, self.oauth_root, self.refresh_token
        )["access_token"]
        return Auth(
            self.gateway,
            new_access_token,
            self.refresh_token,
            self.user_number,
            self.oauth_root,
        )

    def serialize(self) -> Dict[str, str]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_number": self.user_number,
            "oauth_root": self.oauth_root,
        }


class Session(object):
    def __init__(self, auth, session_id=None) -> None:
        self.auth = auth
        self.session_id = session_id

    def post(self, path, data=None):
        """Make a POST request to the API server.

        This is like `lgedm_post`, but it pulls the context for the
        request from an active Session.
        """

        url = urljoin(self.auth.gateway.api_root + "/", path)
        return thinq_request(
            RequestMethod.POST,
            url,
            data,
            access_token=self.auth.access_token,
            user_number=self.auth.user_number,
            country=self.auth.gateway.country,
            language=self.auth.gateway.language,
        )

    def get(self, path):
        """Make a GET request to the API server.

        This is like `lgedm_get`, but it pulls the context for the
        request from an active Session.
        """

        url = urljoin(self.auth.gateway.api_root + "/", path)
        return thinq_request(
            RequestMethod.GET,
            url,
            access_token=self.auth.access_token,
            user_number=self.auth.user_number,
            country=self.auth.gateway.country,
            language=self.auth.gateway.language,
        )

    def get_devices(self) -> List[Dict[str, Any]]:
        """Get a list of devices associated with the user's account.

        Return a list of dicts with information about the devices.
        """

        return get_list(self.get("service/application/dashboard"), "item")

    def monitor_start(self, device_id):
        """Begin monitoring a device's status.

        Return a "work ID" that can be used to retrieve the result of
        monitoring.
        """

        res = self.post(
            "rti/rtiMon",
            {
                "cmd": "Mon",
                "cmdOpt": "Start",
                "deviceId": device_id,
                "workId": gen_uuid(),
            },
        )
        return res["workId"]

    def monitor_poll(self, device_id, work_id):
        """Get the result of a monitoring task.

        `work_id` is a string ID retrieved from `monitor_start`. Return
        a status result, which is a bytestring, or None if the
        monitoring is not yet ready.

        May raise a `MonitorError`, in which case the right course of
        action is probably to restart the monitoring task.
        """

        work_list = [{"deviceId": device_id, "workId": work_id}]
        res = self.post("rti/rtiResult", {"workList": work_list})["workList"]

        # When monitoring first starts, it usually takes a few
        # iterations before data becomes available. In the initial
        # "warmup" phase, `returnCode` is missing from the response.
        if "returnCode" not in res:
            return None

        # Check for errors.
        code = res.get("returnCode")  # returnCode can be missing.
        if code != "0000":
            raise MonitorError(device_id, code)

        # The return data may or may not be present, depending on the
        # monitoring task status.
        if "returnData" in res:
            # The main response payload is base64-encoded binary data in
            # the `returnData` field. This sometimes contains JSON data
            # and sometimes other binary data.
            return base64.b64decode(res["returnData"])
        else:
            return None

    def monitor_stop(self, device_id, work_id):
        """Stop monitoring a device."""

        self.post(
            "rti/rtiMon",
            {
                "cmd": "Mon",
                "cmdOpt": "Stop",
                "deviceId": device_id,
                "workId": work_id,
            },
        )

    def device_control(self, device_id, data):
        """Control a device's settings.

        `values` is a key/value map containing the settings to update.
        """

        controlPath = "service/devices/{}/control-sync".format(device_id)

        res = self.post(controlPath, data)
        return res
