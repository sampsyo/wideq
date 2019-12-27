import enum
from typing import Optional

from .client import Device, _UNKNOWN
from .util import lookup_enum, lookup_reference


class IcePlus(enum.Enum):

    OFF = "@CP_OFF_EN_W"
    ON = "@CP_ON_EN_W"
    ICE_PLUS = "@RE_TERM_ICE_PLUS_W"
    ICE_PLUS_FREEZE = "@RE_MAIN_SPEED_FREEZE_TERM_W"
    ICE_PLUS_OFF = "@CP_TERM_OFF_KO_W"


class FreshAirFilter(enum.Enum):

    OFF = "@CP_TERM_OFF_KO_W"
    AUTO = "@RE_STATE_FRESH_AIR_FILTER_MODE_AUTO_W"
    POWER = "@RE_STATE_FRESH_AIR_FILTER_MODE_POWER_W"
    REPLACE_FILTER = "@RE_STATE_REPLACE_FILTER_W"
    SMARTCARE_ON = "@RE_STATE_SMART_SMART_CARE_ON"
    SMARTCARE_OFF = "@RE_STATE_SMART_SMART_CARE_OFF"
    SMARTCARE_WAIT = "@RE_STATE_SMART_SMART_CARE_WAIT"
    EMPTY = ""


class SmartSavingMode(enum.Enum):

    OFF = "@CP_TERM_USE_NOT_W"
    NIGHT = "@RE_SMARTSAVING_MODE_NIGHT_W"
    CUSTOM = "@RE_SMARTSAVING_MODE_CUSTOM_W"
    EMPTY = ""


class SmartSavingModeStatus(enum.Enum):

    OFF = "OFF"
    ON = "ON"
    EMPTY = ""


class EcoFriendly(enum.Enum):

    OFF = "@CP_OFF_EN_W"
    ON = "@CP_ON_EN_W"


class LockingStatus(enum.Enum):

    UNLOCK = "UNLOCK"
    LOCK = "LOCK"


class DoorOpenState(enum.Enum):

    OPEN = "OPEN"
    CLOSE = "CLOSE"
    EMPTY = ""
    UNKNOWN = _UNKNOWN


class RefrigeratorDevice(Device):
    """A higher-level interface for a refrigerator."""

    def set_temp_refrigerator_c(self, temp_refrigerator):

        temp_refrigerator_value = self.model.enum_value('TempRefrigerator', str(temp_refrigerator))
        # '{"RETM":"{{TempRefrigerator}}", "REFT":"{{TempFreezer}}", "REIP":"{{IcePlus}}", "REEF":"{{EcoFriendly}}" }'
        self._set_control('RETM', temp_refrigerator_value)

    def set_temp_freezer_c(self, temp_freezer):

        temp_freezer_value = self.model.enum_value('TempFreezer', str(temp_freezer))
        self._set_control('REFT', temp_freezer_value)

    def poll(self) -> Optional['RefrigeratorStatus']:
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`.

        :returns: Either a `RefrigeratorStatus` instance or `None` if the status is
            not yet available.
        """
        # Abort if monitoring has not started yet.
        if not hasattr(self, 'mon'):
            return None

        data = self.mon.poll()
        if data:
            res = self.model.decode_monitor(data)
            return RefrigeratorStatus(self, res)
        else:
            return None


class RefrigeratorStatus(object):
    """Higher-level information about a refrigerator's current status.

    :param refrigerator: The RefrigeratorDevice instance.
    :param data: JSON data from the API.
    """

    def __init__(self, refrigerator: RefrigeratorDevice, data: dict):
        self.refrigerator = refrigerator
        self.data = data

    @property
    def temp_refrigerator_c(self):
        return int(lookup_enum('TempRefrigerator', self.data, self.refrigerator))

    @property
    def temp_freezer_c(self):
        return int(lookup_enum('TempFreezer', self.data, self.refrigerator))

    @property
    def ice_plus_status(self):
        return IcePlus(lookup_enum('IcePlus', self.data, self.refrigerator))

    @property
    def fresh_air_filter_status(self):
        return FreshAirFilter(lookup_enum('FreshAirFilter', self.data, self.refrigerator))

    @property
    def energy_saving_mode(self):
        return SmartSavingMode(lookup_enum('SmartSavingMode', self.data, self.refrigerator))

    @property
    def door_opened(self):
        door = DoorOpenState(lookup_enum('DoorOpenState', self.data, self.refrigerator))
        return door == DoorOpenState.OPEN

    @property
    def temp_unit(self):
        return lookup_enum('TempUnit', self.data, self.refrigerator)

    @property
    def energy_saving_enabled(self):
        status = SmartSavingModeStatus(lookup_enum('SmartSavingModeStatus', self.data, self.refrigerator))
        return status == SmartSavingModeStatus.ON

    @property
    def locked(self):
        status = LockingStatus(lookup_enum('LockingStatus', self.data, self.refrigerator))
        return status == LockingStatus.LOCK

    @property
    def active_saving_status(self):
        return self.data['ActiveSavingStatus']

    @property
    def eco_enabled(self):
        eco = EcoFriendly(lookup_enum('EcoFriendly', self.data, self.refrigerator))
        return eco == EcoFriendly.ON

    @property
    def water_filter_used_month(self):
        return self.data['WaterFilterUsedMonth']
