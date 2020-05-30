"""A high-level, convenient abstraction for interacting with the LG
SmartThinQ API for most use cases.
"""
import json
import enum
import logging
import os
import requests
import base64
from collections import namedtuple
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

from . import core

#: Represents an unknown enum value.
_UNKNOWN = 'Unknown'

MIN_TIME_BETWEEN_UPDATE = 25  # seconds
LOGGER = logging.getLogger("wideq.client")


class Monitor(object):
    """A monitoring task for a device.

    This task is robust to some API-level failures. If the monitoring
    task expires, it attempts to start a new one automatically. This
    makes one `Monitor` object suitable for long-term monitoring.
    """

    def __init__(self, session: core.Session, device_id: str) -> None:
        self.session = session
        self.device_id = device_id

    def start(self) -> None:
        self.work_id = self.session.monitor_start(self.device_id)

    def stop(self) -> None:
        self.session.monitor_stop(self.device_id, self.work_id)

    def poll(self) -> Optional[bytes]:
        """Get the current status data (a bytestring) or None if the
        device is not yet ready.
        """

        try:
            return self.session.monitor_poll(self.device_id, self.work_id)
        except core.MonitorError:
            # Try to restart the task.
            self.stop()
            self.start()
            return None

    @staticmethod
    def decode_json(data: bytes) -> Dict[str, Any]:
        """Decode a bytestring that encodes JSON status data."""

        return json.loads(data.decode('utf8'))

    def poll_json(self) -> Optional[Dict[str, Any]]:
        """For devices where status is reported via JSON data, get the
        decoded status result (or None if status is not available).
        """

        data = self.poll()
        return self.decode_json(data) if data else None

    def __enter__(self) -> 'Monitor':
        self.start()
        return self

    def __exit__(self, type, value, tb) -> None:
        self.stop()


class Client(object):
    """A higher-level API wrapper that provides a session more easily
        and allows serialization of state.
        """

    def __init__(
            self,
            gateway: Optional[core.Gateway] = None,
            auth: Optional[core.Auth] = None,
            session: Optional[core.Session] = None,
            country: str = core.DEFAULT_COUNTRY,
            language: str = core.DEFAULT_LANGUAGE,
    ) -> None:
        # The three steps required to get access to call the API.
        self._gateway: Optional[core.Gateway] = gateway
        self._auth: Optional[core.Auth] = auth
        self._session: Optional[core.Session] = session
        self._last_device_update = datetime.now()

        # The last list of devices we got from the server. This is the
        # raw JSON list data describing the devices.
        self._devices = None

        # Cached model info data. This is a mapping from URLs to JSON
        # responses.
        self._model_info: Dict[str, Any] = {}

        # Locale information used to discover a gateway, if necessary.
        self._country = country
        self._language = language

    def _inject_thinq2_device(self):
        """This is used only for debug"""
        data_file = os.path.dirname(os.path.realpath(__file__)) + "/deviceV2.txt"
        with open(data_file, "r") as f:
            device_v2 = json.load(f)
        for d in device_v2:
            self._devices.append(d)
            LOGGER.debug("Injected debug device: %s", d)

    def _load_devices(self, force_update: bool = False):
        if self._session and (self._devices is None or force_update):
            self._devices = self._session.get_devices()
            # for debug
            # self._inject_thinq2_device()
            # for debug

    @property
    def gateway(self) -> core.Gateway:
        if not self._gateway:
            self._gateway = core.Gateway.discover(self._country, self._language)
        return self._gateway

    @property
    def auth(self) -> core.Auth:
        if not self._auth:
            assert False, "unauthenticated"
        return self._auth

    @property
    def session(self) -> core.Session:
        if not self._session:
            self._session = self.auth.start_session()
            self._load_devices()
        return self._session

    @property
    def hasdevices(self) -> bool:
        return True if self._devices else False

    @property
    def devices(self) -> Generator["DeviceInfo", None, None]:
        """DeviceInfo objects describing the user's devices.
            """
        if self._devices is None:
            self._load_devices()
        return (DeviceInfo(d) for d in self._devices)

    def refresh_devices(self):
        """Update DeviceInfo objects from Gateway to update snapshot
            for Thinq2 devices.
            """
        call_time = datetime.now()
        difference = (call_time - self._last_device_update).total_seconds()
        if difference > MIN_TIME_BETWEEN_UPDATE:
            self._load_devices(True)
            self._last_device_update = call_time

    def get_device(self, device_id) -> Optional["DeviceInfo"]:
        """Look up a DeviceInfo object by device ID.

        Return None if the device does not exist.
        """
        for device in self.devices:
            if device.id == device_id:
                return device
        return None

    @classmethod
    def load(cls, state: Dict[str, Any]) -> "Client":
        """Load a client from serialized state.
            """

        client = cls()

        if "gateway" in state:
            data = state["gateway"]
            client._gateway = core.Gateway(
                data["auth_base"],
                data["api_root"],
                data["api2_root"],
                data.get("country", core.DEFAULT_COUNTRY),
                data.get("language", core.DEFAULT_LANGUAGE),
            )

        if "auth" in state:
            data = state["auth"]
            client._auth = core.Auth.load(client._gateway, data)

        if "session" in state:
            client._session = core.Session(client.auth, state["session"])

        if "model_info" in state:
            client._model_info = state["model_info"]

        if "country" in state:
            client._country = state["country"]

        if "language" in state:
            client._language = state["language"]

        return client

    def dump(self) -> Dict[str, Any]:
        """Serialize the client state."""

        out = {
            "model_info": self._model_info,
        }

        if self._gateway:
            out["gateway"] = {
                "auth_base": self._gateway.auth_base,
                "api_root": self._gateway.api_root,
                "api2_root": self._gateway.api2_root,
                "country": self._gateway.country,
                "language": self._gateway.language,
            }

        if self._auth:
            out["auth"] = {
                "access_token": self._auth.access_token,
                "refresh_token": self._auth.refresh_token,
            }

        if self._session:
            out["session"] = self._session.session_id

        out["country"] = self._country
        out["language"] = self._language

        return out

    def refresh(self) -> None:
        self._auth = self.auth.refresh()
        self._session = self.auth.start_session()
        # self._device = None
        self._load_devices()

    @classmethod
    def from_token(
            cls, oauth_url, refresh_token, user_number, country=None, language=None
    ) -> "Client":
        """Construct a client using just a refresh token.

            This allows simpler state storage (e.g., for human-written
            configuration) but it is a little less efficient because we need
            to reload the gateway servers and restart the session.
            """

        client = cls(
            country=country or core.DEFAULT_COUNTRY,
            language=language or core.DEFAULT_LANGUAGE,
        )
        client._auth = core.Auth(
            client.gateway, oauth_url, None, refresh_token, user_number
        )
        client.refresh()
        return client

    @classmethod
    def oauthinfo_from_url(cls, url):
        """Create an authentication using an OAuth callback URL.
        """
        oauth_url, auth_code, user_number = core.parse_oauth_callback(url)
        access_token, refresh_token = core.login(oauth_url, auth_code)

        return {
            "oauth_url": oauth_url,
            "user_number": user_number,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def model_info(self, device):
        """For a DeviceInfo object, get a ModelInfo object describing
            the model's capabilities.
            """
        url = device.model_info_url
        if url not in self._model_info:
            LOGGER.info(
                "Loading model info for %s. Model: %s, Url: %s",
                device.name,
                device.model_name,
                url,
            )
            self._model_info[url] = device.load_model_info()
        return self._model_info[url]


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


class PlatformType(enum.Enum):
    """The category of device."""

    THINQ1 = "thinq1"
    THINQ2 = "thinq2"
    UNKNOWN = _UNKNOWN


class DeviceInfo(object):
    """Details about a user's device.

    This is populated from a JSON dictionary provided by the API.
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def _get_data_key(self, keys):
        for key in keys:
            if key in self._data:
                return key
        return ""

    def _get_data_value(self, key):
        if isinstance(key, list):
            vkey = self._get_data_key(key)
        else:
            vkey = key

        return self._data.get(vkey, _UNKNOWN)

    @property
    def model_id(self) -> str:
        return self._get_data_value(["modelName", "modelNm"])

    @property
    def id(self) -> str:
        return self._get_data_value("deviceId")

    @property
    def model_info_url(self) -> str:
        return self._get_data_value(["modelJsonUrl", "modelJsonUri"])

    @property
    def name(self) -> str:
        return self._get_data_value("alias")

    @property
    def macaddress(self) -> str:
        return self._get_data_value("macAddress")

    @property
    def model_name(self) -> str:
        return self._get_data_value(["modelName", "modelNm"])

    @property
    def firmware(self) -> str:
        return self._get_data_value("fwVer")

    @property
    def devicestate(self) -> str:
        """The kind of device, as a `DeviceType` value."""
        return self._get_data_value("deviceState")

    @property
    def isonline(self) -> bool:
        """The kind of device, as a `DeviceType` value."""
        return self._data.get("online", False)

    @property
    def type(self) -> DeviceType:
        """The kind of device, as a `DeviceType` value."""
        return DeviceType(self._get_data_value("deviceType"))

    @property
    def platform_type(self) -> PlatformType:
        """The kind of device, as a `DeviceType` value."""
        ptype = self._data.get("platformType")
        if not ptype:
            return (
                PlatformType.THINQ1
            )  # for the moment, probably not available in APIv1
        return PlatformType(ptype)

    @property
    def snapshot(self) -> Optional[Dict[str, Any]]:
        if "snapshot" in self._data:
            return self._data["snapshot"]
        return None

    def load_model_info(self):
        """Load JSON data describing the model's capabilities.
        """
        info_url = self.model_info_url
        if info_url == _UNKNOWN:
            return {}
        return requests.get(info_url, timeout=core.DEFAULT_TIMEOUT).json()


BitValue = namedtuple('BitValue', ['options'])
EnumValue = namedtuple('EnumValue', ['options'])
RangeValue = namedtuple('RangeValue', ['min', 'max', 'step'])
#: This is a value that is a reference to another key in the data that is at
#: the same level as the `Value` key.
ReferenceValue = namedtuple('ReferenceValue', ['reference'])
StringValue = namedtuple('StringValue', ['comment'])


class ModelInfo(object):
    """A description of a device model's capabilities.
    """

    def __init__(self, data):
        self.data = data
        self._bit_keys = {}

    @property
    def is_info_v2(self):
        return False

    def value(self, name: str):
        """Look up information about a value.

        :param name: The name to look up.
        :returns: One of (`BitValue`, `EnumValue`, `RangeValue`,
            `ReferenceValue`, `StringValue`).
        :raises ValueError: If an unsupported type is encountered.
        """
        d = self.data['Value'][name]
        if d['type'] in ('Enum', 'enum'):
            return EnumValue(d['option'])
        elif d['type'] == 'Range':
            return RangeValue(
                d['option']['min'], d['option']['max'],
                d['option'].get('step', 1)
            )
        elif d['type'].lower() == 'bit':
            bit_values = {opt['startbit']: opt['value'] for opt in d['option']}
            return BitValue(bit_values)
        elif d['type'].lower() == 'reference':
            ref = d['option'][0]
            return ReferenceValue(self.data[ref])
        elif d['type'].lower() == 'string':
            return StringValue(d.get('_comment', ''))
        else:
            raise ValueError(
                f"unsupported value name: '{name}'"
                f" type: '{str(d['type'])}' data: '{str(d)}'")

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
        if value not in options:
            LOGGER.warning(
                'Value `%s` for key `%s` not in options: %s. Values from API: '
                '%s', value, key, options, self.data['Value'][key]['option'])
            return _UNKNOWN
        return options[value]

    def reference_name(self, key: str, value: Any) -> Optional[str]:
        """Look up the friendly name for an encoded reference value.

        :param key: The referenced key.
        :param value: The value whose name we want to look up.
        :returns: The friendly name for the referenced value.  If no name
            can be found None will be returned.
        """
        value = str(value)
        reference = self.value(key).reference
        if value in reference:
            return reference[value]['_comment']
        return None

    def _get_bit_key(self, key):

        def search_bit_key(key, data):
            if not data:
                return {}
            for i in range(1, 4):
                opt_key = f"Option{str(i)}"
                option = data.get(opt_key)
                if not option:
                    continue
                for opt in option.get("option", []):
                    if key == opt.get("value", ""):
                        start_bit = opt.get("startbit")
                        length = opt.get("length", 1)
                        if start_bit is None:
                            return {}
                        return {
                            "option": opt_key,
                            "startbit": start_bit,
                            "length": length,
                        }
            return {}

        bit_key = self._bit_keys.get(key)
        if bit_key is None:
            data = self.data.get("Value")
            bit_key = search_bit_key(key, data)
            self._bit_keys[key] = bit_key

        return bit_key

    def bit_value(self, key, values):
        """Look up the bit value for an specific key
        """
        bit_key = self._get_bit_key(key)
        if not bit_key:
            return None
        value = None if not values else values.get(bit_key["option"])
        if not value:
            return "0"
        bit_value = int(value)
        start_bit = bit_key["startbit"]
        length = bit_key["length"]
        val = 0
        for i in range(0, length):
            bit_index = 2 ** (start_bit + i)
            bit = 1 if bit_value & bit_index else 0
            val += bit * (2 ** i)
        return str(val)

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

    def __init__(self, client: Client, device: DeviceInfo):
        """Create a wrapper for a `DeviceInfo` object associated with a
        `Client`.
        """
        self.client = client
        self.device = device
        self.model: ModelInfo = client.model_info(device)
        self._should_poll = device.platform_type == PlatformType.THINQ1

    def _set_control(self, key, value):
        """Set a device's control for `key` to `value`."""
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
        """Look up a device's control value."""
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
        if not self._should_poll:
            return
        mon = Monitor(self.client.session, self.device.id)
        mon.start()
        self.mon = mon

    def monitor_stop(self):
        """Stop monitoring the device's status."""
        if not self._should_poll:
            return
        self.mon.stop()
