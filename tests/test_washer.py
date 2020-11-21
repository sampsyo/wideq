import json
import unittest

from wideq.client import Client, DeviceInfo
from wideq.washer import WasherDevice, WasherState, WasherStatus


POLL_DATA = {
    "APCourse": "10",
    "DryLevel": "0",
    "Error": "0",
    "Initial_Time_H": "0",
    "Initial_Time_M": "58",
    "LoadLevel": "4",
    "OPCourse": "0",
    "Option1": "0",
    "Option2": "0",
    "Option3": "2",
    "PreState": "23",
    "Remain_Time_H": "0",
    "Remain_Time_M": "13",
    "Reserve_Time_H": "0",
    "Reserve_Time_M": "0",
    "RinseOption": "1",
    "SmartCourse": "51",
    "Soil": "0",
    "SpinSpeed": "5",
    "State": "30",
    "TCLCount": "15",
    "WaterTemp": "4",
}


class WasherStatusTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        with open("./tests/fixtures/client.json") as fp:
            state = json.load(fp)
        self.client = Client.load(state)
        self.device_info = DeviceInfo(
            {
                "alias": "WASHER",
                "deviceId": "33330ba80-107d-11e9-96c8-0051ede85d3f",
                "deviceType": 201,
                "modelJsonUrl": (
                    "https://aic.lgthinq.com:46030/api/webContents/modelJSON?"
                    "modelName=F3L2CYV5W_WIFI&countryCode=WW&contentsId="
                    "JS1217232703654216&authKey=thinq"
                ),
                "modelNm": "F3L2CYV5W_WIFI",
            }
        )
        self.washer = WasherDevice(self.client, self.device_info)

    def test_properties(self):
        status = WasherStatus(self.washer, POLL_DATA)
        self.assertEqual(WasherState.RINSING, status.state)
        self.assertEqual(WasherState.RUNNING, status.previous_state)
        self.assertTrue(status.is_on)
        self.assertEqual(13, status.remaining_time)
        self.assertEqual(58, status.initial_time)
        self.assertEqual("Towels", status.course)
        self.assertEqual("SmallLoad", status.smart_course)
        self.assertEqual("No Error", status.error)
