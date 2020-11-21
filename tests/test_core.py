import unittest
import responses

import wideq.core


class SimpleTest(unittest.TestCase):
    @responses.activate
    def test_gateway_en_US(self):
        responses.add(
            responses.POST,
            "https://kic.lgthinq.com:46030/api/common/gatewayUriList",
            json={
                "lgedmRoot": {
                    "thinqUri": "https://aic.lgthinq.com:46030/api",
                    "empUri": "https://us.m.lgaccount.com",
                    "oauthUri": "https://us.lgeapi.com",
                    "countryCode": "US",
                    "langCode": "en-US",
                }
            },
        )
        gatewayInstance = wideq.core.Gateway.discover("US", "en-US")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(gatewayInstance.country, "US")
        self.assertEqual(gatewayInstance.language, "en-US")
        self.assertEqual(
            gatewayInstance.auth_base, "https://us.m.lgaccount.com"
        )
        self.assertEqual(
            gatewayInstance.api_root, "https://aic.lgthinq.com:46030/api"
        )
        self.assertEqual(gatewayInstance.oauth_root, "https://us.lgeapi.com")

    @responses.activate
    def test_gateway_en_NO(self):
        responses.add(
            responses.POST,
            "https://kic.lgthinq.com:46030/api/common/gatewayUriList",
            json={
                "lgedmRoot": {
                    "countryCode": "NO",
                    "langCode": "en-NO",
                    "thinqUri": "https://eic.lgthinq.com:46030/api",
                    "empUri": "https://no.m.lgaccount.com",
                    "oauthUri": "https://no.lgeapi.com",
                }
            },
        )
        gatewayInstance = wideq.core.Gateway.discover("NO", "en-NO")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(gatewayInstance.country, "NO")
        self.assertEqual(gatewayInstance.language, "en-NO")
        self.assertEqual(
            gatewayInstance.auth_base, "https://no.m.lgaccount.com"
        )
        self.assertEqual(
            gatewayInstance.api_root, "https://eic.lgthinq.com:46030/api"
        )
        self.assertEqual(gatewayInstance.oauth_root, "https://no.lgeapi.com")
