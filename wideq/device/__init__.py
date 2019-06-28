import base64
import enum
import json
from collections import namedtuple

import requests

from ..monitor import Monitor


EnumValue = namedtuple('EnumValue', ['options'])
RangeValue = namedtuple('RangeValue', ['min', 'max', 'step'])


class DeviceType(enum.Enum):
    """The category of device."""

    REFRIGERATOR = 101
    KIMCHI_REFRIGERATOR = 102
    WATER_PURIFIER = 103
    WASHER = 201
    DRYER = 202
    STYLER = 203
    DISHWASHER = 204
    OVEN = 301
    MICROWAVE = 302
    COOKTOP = 303
    HOOD = 304
    AC = 401  # Includes heat pumps, etc., possibly all HVAC devices.
    AIR_PURIFIER = 402
    DEHUMIDIFIER = 403
    ROBOT_KING = 501  # Robotic vacuum cleaner?
    ARCH = 1001
    MISSG = 3001
    SENSOR = 3002
    SOLAR_SENSOR = 3102
    IOT_LIGHTING = 3003
    IOT_MOTION_SENSOR = 3004
    IOT_SMART_PLUG = 3005
    IOT_DUST_SENSOR = 3006
    EMS_AIR_STATION = 4001
    AIR_SENSOR = 4003


class DeviceInfo(object):
    """Details about a user's device.

    This is populated from a JSON dictionary provided by the API.
    """

    def __init__(self, data: dict):
        self.data = data

    @property
    def model_id(self):
        return self.data['modelNm']

    @property
    def id(self):
        return self.data['deviceId']

    @property
    def model_info_url(self):
        return self.data['modelJsonUrl']

    @property
    def name(self):
        return self.data['alias']

    @property
    def type(self):
        """The kind of device, as a `DeviceType` value."""

        return DeviceType(self.data['deviceType'])

    def load_model_info(self):
        """Load JSON data describing the model's capabilities."""
        return requests.get(self.model_info_url).json()


class ModelInfo(object):
    """A description of a device model's capabilities.

    :param data: A dict of data about the model.
    """

    def __init__(self, data: dict):
        self.data = data

    def value(self, name: str):
        """Look up information about a value.

        Return either an `EnumValue` or a `RangeValue`.
        """
        d = self.data['Value'][name]
        if d['type'] in ('Enum', 'enum'):
            return EnumValue(d['option'])
        elif d['type'] == 'Range':
            return RangeValue(
                d['option']['min'], d['option']['max'], d['option']['step']
            )
        else:
            # @TODO: raise an exception, do not use assert
            assert False, "unsupported value type {}".format(d['type'])

    def default(self, name):
        """Get the default value, if it exists, for a given value.
        """
        return self.data['Value'][name]['default']

    def enum_value(self, key, name):
        """Look up the encoded value for a friendly enum name.
        """
        options = self.value(key).options
        options_inv = {v: k for k, v in options.items()}  # Invert the map.
        return options_inv[name]

    def enum_name(self, key, value):
        """Look up the friendly enum name for an encoded value.
        """
        options = self.value(key).options
        return options[value]

    @property
    def binary_monitor_data(self):
        """Check that type of monitoring is BINARY(BYTE).
        """
        return self.data['Monitoring']['type'] == 'BINARY(BYTE)'

    def decode_monitor_binary(self, data):
        """Decode binary encoded status data.
        """
        decoded = {}
        for item in self.data['Monitoring']['protocol']:
            key = item['value']
            value = 0
            for v in data[item['startByte']:item['startByte'] +
                          item['length']]:
                value = (value << 8) + v
            decoded[key] = str(value)
        return decoded

    def decode_monitor_json(self, data):
        """Decode a bytestring that encodes JSON status data."""
        return json.loads(data.decode('utf8'))

    def decode_monitor(self, data):
        """Decode  status data."""
        if self.binary_monitor_data:
            return self.decode_monitor_binary(data)
        else:
            return self.decode_monitor_json(data)


class Device(object):
    """A higher-level interface to a specific device.

    Unlike `DeviceInfo`, which just stores data *about* a device,
    `Device` objects refer to their client and can perform operations
    regarding the device.
    """

    def __init__(self, client, device):
        """Create a wrapper for a `DeviceInfo` object associated with a
        `Client`.
        """

        self.client = client
        self.device = device
        self.model = client.model_info(device)

    def _set_control(self, key, value):
        """Set a device's control for `key` to `value`.
        """

        self.client.session.set_device_controls(
            self.device.id,
            {key: value},
        )

    def _get_config(self, key):
        """Look up a device's configuration for a given value.

        The response is parsed as base64-encoded JSON.
        """

        data = self.client.session.get_device_config(
            self.device.id,
            key,
        )
        return json.loads(base64.b64decode(data).decode('utf8'))

    def _get_control(self, key):
        """Look up a device's control value.
        """

        data = self.client.session.get_device_config(
            self.device.id,
            key,
            'Control',
        )

        # The response comes in a funky key/value format: "(key:value)".
        _, value = data[1:-1].split(':')
        return value

    def monitor_start(self):
        """Start monitoring the device's status."""
        mon = Monitor(self.client.session, self.device.id)
        mon.start()
        self.mon = mon

    def monitor_stop(self):
        """Stop monitoring the device's status."""
        self.mon.stop()
