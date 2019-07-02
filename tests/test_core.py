import unittest
import responses
import json

import wideq.core


class SimpleTest(unittest.TestCase):
    @responses.activate
    def test_gateway_info(self):
        responses.add(
            responses.POST,
            'https://kic.lgthinq.com:46030/api/common/gatewayUriList',
            json={'lgedmRoot': 'foo'},
        )

        data = wideq.core.gateway_info('COUNTRY', 'LANGUAGE')
        self.assertEqual(data, 'foo')

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {'lgedmRoot': {'countryCode': 'COUNTRY', 'langCode': 'LANGUAGE'}},
        )
