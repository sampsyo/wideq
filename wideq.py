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


def gateway_info():
    """Load information about the hosts to use for API interaction.
    """

    req_data = {DATA_ROOT: {'countryCode': COUNTRY, 'langCode': LANGUAGE}}
    headers = {
        'x-thinq-application-key': APP_KEY,
        'x-thinq-security-key': SECURITY_KEY,
        'Accept': 'application/json',
    }
    res = requests.post(GATEWAY_URL, json=req_data, headers=headers)
    return res.json()[DATA_ROOT]


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
    req_data = {DATA_ROOT: {
        'countryCode': COUNTRY,
        'langCode': LANGUAGE,
        'loginType': 'EMP',
        'token': access_token,
    }}
    headers = {
        'x-thinq-application-key': APP_KEY,
        'x-thinq-security-key': SECURITY_KEY,
        'Accept': 'application/json',
    }
    res = requests.post(url, json=req_data, headers=headers)
    return res.json()[DATA_ROOT]


if __name__ == '__main__':
    gw = gateway_info()
    oauth_base = gw['empUri']
    api_root = gw['thinqUri']
    print(oauth_url(oauth_base))

    access_token = parse_oauth_callback(input())
    print(access_token)

    session_info = login(api_root, access_token)
    print(session_info)
