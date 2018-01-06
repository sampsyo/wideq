import requests
from urllib.parse import urljoin, urlencode


GATEWAY_URL = 'https://kic.lgthinq.com:46030/api/common/gatewayUriList'
APP_KEY = 'wideq'
SECURITY_KEY = 'nuts_securitykey'
DATA_ROOT = 'lgedmRoot'
COUNTRY = 'US'
LANGUAGE = 'en-US'
OAUTH_PATH = '/login/sign_in'
SVC_CODE = 'SVC202'
CLIENT_ID = 'LGAO221A02'


def gateway_info():
    req_data = {DATA_ROOT: {'countryCode': COUNTRY, 'langCode': LANGUAGE}}
    headers = {
        'x-thinq-application-key': APP_KEY,
        'x-thinq-security-key': SECURITY_KEY,
        'Accept': 'application/json',
    }
    res = requests.post(GATEWAY_URL, json=req_data, headers=headers)
    return res.json()[DATA_ROOT]


def oauth_url(oauth_base):
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


if __name__ == '__main__':
    gw = gateway_info()
    oauth_base = gw['empUri']
    api_root = gw['thinqUri']
    print(oauth_url(oauth_base))
