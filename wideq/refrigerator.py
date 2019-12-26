import enum
from typing import Optional

from .client import Device
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


class SmartSavingMode(enum.Enum):

    OFF = "@CP_TERM_USE_NOT_W"
    NIGHT = "@RE_SMARTSAVING_MODE_NIGHT_W"
    CUSTOM = "@RE_SMARTSAVING_MODE_CUSTOM_W"


class SmartSavingModeStatus(enum.Enum):

    OFF = "OFF"
    ON = "ON"


class EcoFriendly(enum.Enum):

    OFF = "@CP_OFF_EN_W"
    ON = "@CP_ON_EN_W"


class LockingStatus(enum.Enum):

    UNLOCK = "UNLOCK"
    LOCK = "LOCK"


class DoorOpenState(enum.Enum):

    OPEN = "OPEN"
    CLOSE = "CLOSE"


class RefrigeratorDevice(Device):
    """A higher-level interface for a refrigerator."""

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

    def lookup_enum(self, key):
        return self.refrigerator.model.enum_name(key, self.data[key])

    @property
    def temprefrigerator_c(self):
        return self.lookup_enum('TempRefrigerator')

    @property
    def tempfreezer_c(self):
        return self.lookup_enum('TempFreezer')

    @property
    def iceplus(self):
        return IcePlus(self.lookup_enum('IcePlus'))

    @property
    def freshairfilter(self):
        return FreshAirFilter(self.lookup_enum('FreshAirFilter'))

    @property
    def smartsavingmode(self):
        return SmartSavingMode(self.lookup_enum('SmartSavingMode'))

    @property
    def dooropenstate(self):
        return DoorOpenState(self.lookup_enum('DoorOpenState'))

    @property
    def tempunit(self):
        return self.lookup_enum('TempUnit')

    @property
    def smartsavingmodestatus(self):
        return SmartSavingModeStatus(self.lookup_enum('SmartSavingModeStatus'))

    @property
    def lockingstatus(self):
        return LockingStatus(self.lookup_enum('LockingStatus'))

    @property
    def activesavingstatus(self):
        return self.data['ActiveSavingStatus']

    @property
    def ecofriendly(self):
        return EcoFriendly(self.lookup_enum('EcoFriendly'))
