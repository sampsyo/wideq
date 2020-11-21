import json
import unittest

from wideq.client import Client, DeviceInfo
from wideq.dishwasher import (
    DishWasherDevice,
    DishWasherState,
    DishWasherStatus,
)

POLL_DATA = {
    "16~19": "0",
    "21~22": "0",
    "Course": "2",
    "CourseType": "1",
    "CurDownload": "2",
    "Error": "0",
    "Initial_Time_H": "3",
    "Initial_Time_M": "14",
    "Option1": "208",
    "Option2": "8",
    "Option3": "0",
    "Process": "2",
    "Remain_Time_H": "1",
    "Remain_Time_M": "59",
    "Reserve_Time_H": "0",
    "Reserve_Time_M": "0",
    "RinseLevel": "2",
    "SmartCourse": "2",
    "SofteningLevel": "0",
    "State": "2",
}


class DishWasherStatusTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        with open("./tests/fixtures/client.json") as fp:
            state = json.load(fp)
        self.client = Client.load(state)
        self.device_info = DeviceInfo(
            {
                "alias": "DISHWASHER",
                "deviceId": "33330ba80-107d-11e9-96c8-0051ede8ad3c",
                "deviceType": 204,
                "modelJsonUrl": (
                    "https://aic.lgthinq.com:46030/api/webContents/modelJSON?"
                    "modelName=D3210&countryCode=WW&contentsId="
                    "JS0719082250749334&authKey=thinq"
                ),
                "modelNm": "D3210",
            }
        )
        self.dishwasher = DishWasherDevice(self.client, self.device_info)

    def test_properties(self):
        status = DishWasherStatus(self.dishwasher, POLL_DATA)
        self.assertEqual(DishWasherState.RUNNING, status.state)
        self.assertTrue(status.is_on)
        self.assertEqual(119, status.remaining_time)
        self.assertEqual(194, status.initial_time)
        self.assertEqual("Heavy", status.course)
        self.assertEqual("Casseroles", status.smart_course)
        self.assertEqual("No Error", status.error)
