import json
import unittest

from wideq.client import Client, DeviceInfo
from wideq.dryer import DryerDevice, DryLevel, DryerState, DryerStatus


POLL_DATA = {
    'Course': '5',
    'CurrentDownloadCourse': '100',
    'DryLevel': '0',
    'Error': '0',
    'Initial_Time_H': '0',
    'Initial_Time_M': '1',
    'LoadItem': '0',
    'MoreLessTime': '0',
    'Option1': '64',
    'Option2': '168',
    'PreState': '4',
    'Remain_Time_H': '0',
    'Remain_Time_M': '1',
    'SmartCourse': '0',
    'State': '0',
    'TempControl': '0',
    'TimeDry': '0',
}


class DryerStatusTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        with open('./tests/fixtures/client.json') as fp:
            state = json.load(fp)
        self.client = Client.load(state)
        self.device_info = DeviceInfo({
            'alias': 'DRYER',
            'deviceId': '33330ba80-107d-11e9-96c8-0051ede85d3f',
            'deviceType': 202,
            'modelJsonUrl': (
                'https://aic.lgthinq.com:46030/api/webContents/modelJSON?'
                'modelName=RV13B6ES_D_US_WIFI&countryCode=WW&contentsId='
                'JS11260025236447318&authKey=thinq'),
            'modelNm': 'RV13B6ES_D_US_WIFI',
        })
        self.dryer = DryerDevice(self.client, self.device_info)

    def test_properties(self):
        status = DryerStatus(self.dryer, POLL_DATA)
        self.assertEqual(DryerState.OFF, status.state)
        self.assertEqual(DryerState.END, status.previous_state)
        self.assertEqual(DryLevel.OFF, status.dry_level)
        self.assertFalse(status.is_on)
        self.assertEqual('0', status.remain_time_hours)
        self.assertEqual('1', status.remain_time_minutes)
        self.assertEqual('0', status.initial_time_hours)
        self.assertEqual('1', status.initial_time_minutes)
        self.assertEqual('Delicates', status.course)
        self.assertEqual('Off', status.smart_course)
        self.assertEqual('No Error', status.error)
