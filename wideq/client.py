"""A high-level, convenient abstraction for interacting with the LG
SmartThinQ API for most use cases.
"""
import json
import enum
import logging
import requests
import base64
import re
from collections import namedtuple
from typing import Any, Dict, Generator, List, Optional

from . import core


#: Represents an unknown enum value.
_UNKNOWN = "Unknown"
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

        return json.loads(data.decode("utf8"))

    def poll_json(self) -> Optional[Dict[str, Any]]:
        """For devices where status is reported via JSON data, get the
        decoded status result (or None if status is not available).
        """

        data = self.poll()
        return self.decode_json(data) if data else None

    def __enter__(self) -> "Monitor":
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

        # The last list of devices we got from the server. This is the
        # raw JSON list data describing the devices.
        self._devices: List[Dict[str, Any]] = []

        # Cached model info data. This is a mapping from URLs to JSON
        # responses.
        self._model_info: Dict[str, Any] = {}

        # Locale information used to discover a gateway, if necessary.
        self._country: str = country
        self._language: str = language

    @property
    def gateway(self) -> core.Gateway:
        if not self._gateway:
            self._gateway = core.Gateway.discover(
                self._country, self._language
            )
        return self._gateway

    @property
    def auth(self) -> core.Auth:
        if not self._auth:
            assert False, "unauthenticated"
        return self._auth

    @property
    def session(self) -> core.Session:
        if not self._session:
            self._session, self._devices = self.auth.start_session()
        return self._session

    @property
    def devices(self) -> Generator["DeviceInfo", None, None]:
        """DeviceInfo objects describing the user's devices."""

        if not self._devices:
            self._devices = self.session.get_devices()
        return (DeviceInfo(d) for d in self._devices)

    def get_device(self, device_id) -> Optional["DeviceInfo"]:
        """Look up a DeviceInfo object by device ID.

        Return None if the device does not exist.
        """

        for device in self.devices:
            if device.id == device_id:
                return device
        return None

    def get_device_obj(self, device_id):
        """Look up a subclass of Device object by device ID.

        Return a Device instance if no subclass exists for the device type.
        Return None if the device does not exist.
        """
        from . import util

        device_info = self.get_device(device_id)
        if not device_info:
            return None
        classes = util.device_classes()
        if device_info.type in classes:
            return classes[device_info.type](self, device_info)
        LOGGER.debug(
            "No specific subclass for deviceType %s, using default",
            device_info.type,
        )
        return Device(self, device_info)

    @classmethod
    def load(cls, state: Dict[str, Any]) -> "Client":
        """Load a client from serialized state."""

        client = cls()

        if "gateway" in state:
            client._gateway = core.Gateway.deserialize(state["gateway"])

        if "auth" in state:
            data = state["auth"]
            client._auth = core.Auth(
                client.gateway, data["access_token"], data["refresh_token"]
            )

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

        out: Dict[str, Any] = {
            "model_info": self._model_info,
        }

        if self._gateway:
            out["gateway"] = self._gateway.serialize()

        if self._auth:
            out["auth"] = self._auth.serialize()

        if self._session:
            out["session"] = self._session.session_id

        out["country"] = self._country
        out["language"] = self._language

        return out

    def refresh(self) -> None:
        self._auth = self.auth.refresh()
        self._session, self._devices = self.auth.start_session()

    @classmethod
    def from_token(
        cls, refresh_token, country=None, language=None
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
        client._auth = core.Auth(client.gateway, None, refresh_token)
        client.refresh()
        return client

    def model_info(self, device: "DeviceInfo") -> "ModelInfo":
        """For a DeviceInfo object, get a ModelInfo object describing
        the model's capabilities.
        """
        url = device.model_info_url
        if url not in self._model_info:
            self._model_info[url] = device.load_model_info()
        return ModelInfo(self._model_info[url])


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

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data

    @property
    def model_id(self) -> str:
        return self.data["modelNm"]

    @property
    def id(self) -> str:
        return self.data["deviceId"]

    @property
    def model_info_url(self) -> str:
        return self.data["modelJsonUrl"]

    @property
    def name(self) -> str:
        return str(self.data["alias"])

    @property
    def type(self) -> DeviceType:
        """The kind of device, as a `DeviceType` value."""

        return DeviceType(self.data["deviceType"])

    def load_model_info(self):
        """Load JSON data describing the model's capabilities."""
        return requests.get(self.model_info_url).json()


BitValue = namedtuple("BitValue", ["options"])
EnumValue = namedtuple("EnumValue", ["options"])
RangeValue = namedtuple("RangeValue", ["min", "max", "step"])
#: This is a value that is a reference to another key in the data that is at
#: the same level as the `Value` key.
ReferenceValue = namedtuple("ReferenceValue", ["reference"])
StringValue = namedtuple("StringValue", ["comment"])


class ModelInfo(object):
    """A description of a device model's capabilities."""

    def __init__(self, data):
        self.data = data

    def value(self, name: str):
        """Look up information about a value.

        :param name: The name to look up.
        :returns: One of (`BitValue`, `EnumValue`, `RangeValue`,
            `ReferenceValue`, `StringValue`).
        :raises ValueError: If an unsupported type is encountered.
        """
        d = self.data["Value"][name]
        if d["type"] in ("Enum", "enum"):
            return EnumValue(d["option"])
        elif d["type"] == "Range":
            return RangeValue(
                d["option"]["min"],
                d["option"]["max"],
                d["option"].get("step", 1),
            )
        elif d["type"].lower() == "bit":
            bit_values = {opt["startbit"]: opt["value"] for opt in d["option"]}
            return BitValue(bit_values)
        elif d["type"].lower() == "reference":
            ref = d["option"][0]
            return ReferenceValue(self.data[ref])
        elif d["type"].lower() == "string":
            return StringValue(d.get("_comment", ""))
        else:
            raise ValueError(
                f"unsupported value name: '{name}'"
                f" type: '{str(d['type'])}' data: '{str(d)}'"
            )

    def default(self, name):
        """Get the default value, if it exists, for a given value."""
        return self.data["Value"][name]["default"]

    def enum_value(self, key, name):
        """Look up the encoded value for a friendly enum name."""
        options = self.value(key).options
        options_inv = {v: k for k, v in options.items()}  # Invert the map.
        return options_inv[name]

    def enum_name(self, key, value):
        """Look up the friendly enum name for an encoded value."""
        options = self.value(key).options
        if value not in options:
            LOGGER.warning(
                "Value `%s` for key `%s` not in options: %s. Values from API: "
                "%s",
                value,
                key,
                options,
                self.data["Value"][key]["option"],
            )
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
            return reference[value]["_comment"]
        return None

    @property
    def binary_monitor_data(self):
        """Check that type of monitoring is BINARY(BYTE)."""
        return self.data["Monitoring"]["type"] == "BINARY(BYTE)"

    def decode_monitor_binary(self, data):
        """Decode binary encoded status data."""
        decoded = {}
        for item in self.data["Monitoring"]["protocol"]:
            key = item["value"]
            value = 0
            for v in data[
                item["startByte"] : item["startByte"] + item["length"]
            ]:
                value = (value << 8) + v
            decoded[key] = str(value)
        return decoded

    def decode_monitor_json(self, data):
        """Decode a bytestring that encodes JSON status data."""
        return json.loads(data.decode("utf8"))

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
        data = base64.b64decode(data).decode("utf8")
        try:
            return json.loads(data)
        except json.decoder.JSONDecodeError:
            # Sometimes, the service returns JSON wrapped in an extra
            # pair of curly braces. Try removing them and re-parsing.
            LOGGER.debug("attempting to fix JSON format")
            try:
                return json.loads(re.sub(r"^\{(.*?)\}$", r"\1", data))
            except json.decoder.JSONDecodeError:
                raise core.MalformedResponseError(data)

    def _get_control(self, key):
        """Look up a device's control value."""
        data = self.client.session.get_device_config(
            self.device.id,
            key,
            "Control",
        )

        # The response comes in a funky key/value format: "(key:value)".
        _, value = data[1:-1].split(":")
        return value

    def monitor_start(self):
        """Start monitoring the device's status."""
        mon = Monitor(self.client.session, self.device.id)
        mon.start()
        self.mon = mon

    def monitor_stop(self):
        """Stop monitoring the device's status."""
        self.mon.stop()
