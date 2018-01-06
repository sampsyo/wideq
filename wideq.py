import requests

GATEWAY_URL = 'https://kic.lgthinq.com:46030/api/common/gatewayUriList'
APP_KEY = 'wideq'
SECURITY_KEY = 'nuts_securitykey'
DATA_ROOT = 'lgedmRoot'


def gateway_info(country='US', lang='en-US'):
    req_data = {DATA_ROOT: {'countryCode': country, 'langCode': lang}}
    headers = {
        'x-thinq-application-key': APP_KEY,
        'x-thinq-security-key': SECURITY_KEY,
        'Accept': 'application/json',
    }
    res = requests.post(GATEWAY_URL, json=req_data, headers=headers)
    return res.json()


if __name__ == '__main__':
    print(gateway_info())
