import json
import unittest
from unittest import mock

from wideq.client import Client, DeviceInfo
from wideq.dryer import (
    DryerDevice,
    DryLevel,
    DryerState,
    DryerStatus,
    TempControl,
    TimeDry,
)


POLL_DATA = {
    "Course": "2",
    "CurrentDownloadCourse": "100",
    "DryLevel": "3",
    "Error": "0",
    "Initial_Time_H": "1",
    "Initial_Time_M": "11",
    "LoadItem": "0",
    "MoreLessTime": "0",
    "Option1": "0",
    "Option2": "168",
    "PreState": "1",
    "Remain_Time_H": "0",
    "Remain_Time_M": "54",
    "SmartCourse": "0",
    "State": "50",
    "TempControl": "4",
    "TimeDry": "0",
}


class DryerStatusTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        with open("./tests/fixtures/client.json") as fp:
            state = json.load(fp)
        self.client = Client.load(state)
        self.device_info = DeviceInfo(
            {
                "alias": "DRYER",
                "deviceId": "33330ba80-107d-11e9-96c8-0051ede85d3f",
                "deviceType": 202,
                "modelJsonUrl": (
                    "https://aic.lgthinq.com:46030/api/webContents/modelJSON?"
                    "modelName=RV13B6ES_D_US_WIFI&countryCode=WW&contentsId="
                    "JS11260025236447318&authKey=thinq"
                ),
                "modelNm": "RV13B6ES_D_US_WIFI",
            }
        )
        self.dryer = DryerDevice(self.client, self.device_info)

    def test_properties(self):
        status = DryerStatus(self.dryer, POLL_DATA)
        self.assertEqual(self.dryer, status.dryer)
        self.assertEqual(POLL_DATA, status.data)
        self.assertEqual(DryerState.DRYING, status.state)
        self.assertEqual(DryerState.INITIAL, status.previous_state)
        self.assertEqual(DryLevel.NORMAL, status.dry_level)
        self.assertTrue(status.is_on)
        self.assertEqual(54, status.remaining_time)
        self.assertEqual(71, status.initial_time)
        self.assertEqual("Towels", status.course)
        self.assertEqual("Off", status.smart_course)
        self.assertEqual("No Error", status.error)
        self.assertEqual(TempControl.MID_HIGH, status.temperature_control)
        self.assertEqual(TimeDry.OFF, status.time_dry)

    @mock.patch("wideq.client.LOGGER")
    def test_properties_unknown_enum_value(self, mock_logging):
        """
        This should not raise an error for an invalid enum value and instead
        use the `UNKNOWN` enum value.
        """
        data = dict(POLL_DATA, State="5000")
        status = DryerStatus(self.dryer, data)
        self.assertEqual(DryerState.UNKNOWN, status.state)
        expected_call = mock.call(
            "Value `%s` for key `%s` not in options: %s. Values from API: %s",
            "5000",
            "State",
            mock.ANY,
            mock.ANY,
        )
        self.assertEqual(expected_call, mock_logging.warning.call_args)
