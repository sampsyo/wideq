import unittest

from wideq.client import (
    BitValue, EnumValue, ModelInfo, RangeValue, ReferenceValue)


DATA = {
    'Value': {
        'AntiBacterial': {
            'default': '0',
            'label': '@WM_DRY27_BUTTON_ANTI_BACTERIAL_W',
            'option': {
                '0': '@CP_OFF_EN_W',
                '1': '@CP_ON_EN_W'
            },
            'type': 'Enum'
        },
        'Course': {
            'option': ['Course'],
            'type': 'Reference',
        },
        'Initial_Time_H': {
            'default': 0,
            'option': {'max': 24, 'min': 0},
            'type': 'Range'
        },
        'Option1': {
            'default': '0',
            'option': [
                {
                    'default': '0',
                    'length': 1,
                    'startbit': 0,
                    'value': 'ChildLock'
                },
                {
                    'default': '0',
                    'length': 1,
                    'startbit': 1,
                    'value': 'ReduceStatic'
                },
                {
                    'default': '0',
                    'length': 1,
                    'startbit': 2,
                    'value': 'EasyIron'
                },
                {
                    'default': '0',
                    'length': 1,
                    'startbit': 3,
                    'value': 'DampDrySingal'
                },
                {
                    'default': '0',
                    'length': 1,
                    'startbit': 4,
                    'value': 'WrinkleCare'
                },
                {
                    'default': '0',
                    'length': 1,
                    'startbit': 7,
                    'value': 'AntiBacterial'
                }
            ],
            'type': 'Bit'
        },
        'Unexpected': {'type': 'Unexpected'},
    },
    'Course': {
        "3": {
          "_comment": "Normal",
          "courseType": "Course",
          "id": 3,
          "name": "@WM_DRY27_COURSE_NORMAL_W",
          "script": "",
          "controlEnable": True,
          "freshcareEnable": True,
          "imgIndex": 61,
        },
    },
}


class ModelInfoTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.model_info = ModelInfo(DATA)

    def test_value_enum(self):
        actual = self.model_info.value('AntiBacterial')
        expected = EnumValue({'0': '@CP_OFF_EN_W', '1': '@CP_ON_EN_W'})
        self.assertEqual(expected, actual)

    def test_value_range(self):
        actual = self.model_info.value('Initial_Time_H')
        expected = RangeValue(min=0, max=24, step=1)
        self.assertEqual(expected, actual)

    def test_value_bit(self):
        actual = self.model_info.value('Option1')
        expected = BitValue({
            0: 'ChildLock',
            1: 'ReduceStatic',
            2: 'EasyIron',
            3: 'DampDrySingal',
            4: 'WrinkleCare',
            7: 'AntiBacterial',
        })
        self.assertEqual(expected, actual)

    def test_value_reference(self):
        actual = self.model_info.value('Course')
        expected = ReferenceValue(DATA['Course'])
        self.assertEqual(expected, actual)

    def test_value_unsupported(self):
        with self.assertRaisesRegex(
                ValueError, 'unsupported value type Unexpected'):
            self.model_info.value('Unexpected')
