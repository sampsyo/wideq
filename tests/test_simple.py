import unittest
import wideq
import responses
import json


class SimpleTest(unittest.TestCase):
    @responses.activate
    def test_gateway_info(self):
        responses.add(
            responses.POST,
            'https://kic.lgthinq.com:46030/api/common/gatewayUriList',
            json={'lgedmRoot': 'foo'},
        )

        data = wideq.gateway_info('COUNTRY', 'LANGUAGE')
        self.assertEqual(data, 'foo')

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {'lgedmRoot': {'countryCode': 'COUNTRY', 'langCode': 'LANGUAGE'}},
        )
