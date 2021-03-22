import unittest
import responses

import wideq.core


class SimpleTest(unittest.TestCase):
    @responses.activate
    def test_gateway_en_US(self):
        responses.add(
            responses.GET,
            "https://route.lgthinq.com:46030/v1/service/application/gateway-uri",
            json={
                "result": {
                    "thinq1Uri": "https://aic.lgthinq.com:46030/api",
                    "thinq2Uri": "https://aic-service.lgthinq.com:46030/v1",
                    "empUri": "https://us.m.lgaccount.com",
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
            gatewayInstance.api_root,
            "https://aic-service.lgthinq.com:46030/v1",
        )

    @responses.activate
    def test_gateway_en_NO(self):
        responses.add(
            responses.GET,
            "https://route.lgthinq.com:46030/v1/service/application/gateway-uri",
            json={
                "result": {
                    "countryCode": "NO",
                    "langCode": "en-NO",
                    "thinq1Uri": "https://eic.lgthinq.com:46030/api",
                    "thinq2Uri": "https://eic-service.lgthinq.com:46030/v1",
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
            gatewayInstance.api_root,
            "https://eic-service.lgthinq.com:46030/v1",
        )
