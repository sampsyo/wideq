import enum
from typing import Optional

from .client import Device
from .util import lookup_enum


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
    SMART_GRID_OFF = "@CP_OFF_EN_W"
    SMART_GRID_DEMAND_RESPONSE = "@RE_TERM_DEMAND_RESPONSE_FUNCTIONALITY_W"
    SMART_GRID_CUSTOM = "@RE_TERM_DELAY_DEFROST_CAPABILITY_W"
    EMPTY = ""


class RefrigeratorDevice(Device):
    """A higher-level interface for a refrigerator."""

    def set_temp_refrigerator_c(self, temp):
        """Set the refrigerator temperature in Celsius."""
        value = self.model.enum_value("TempRefrigerator", str(temp))
        self._set_control("RETM", value)

    def set_temp_freezer_c(self, temp):
        """Set the freezer temperature in Celsius."""
        value = self.model.enum_value("TempFreezer", str(temp))
        self._set_control("REFT", value)

    def poll(self) -> Optional["RefrigeratorStatus"]:
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`.

        :returns: Either a `RefrigeratorStatus` instance or `None` if the
            status is not yet available.
        """
        # Abort if monitoring has not started yet.
        if not hasattr(self, "mon"):
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
        temp = lookup_enum("TempRefrigerator", self.data, self.refrigerator)
        return int(temp)

    @property
    def temp_freezer_c(self):
        temp = lookup_enum("TempFreezer", self.data, self.refrigerator)
        return int(temp)

    @property
    def ice_plus_status(self):
        status = lookup_enum("IcePlus", self.data, self.refrigerator)
        return IcePlus(status)

    @property
    def fresh_air_filter_status(self):
        status = lookup_enum("FreshAirFilter", self.data, self.refrigerator)
        return FreshAirFilter(status)

    @property
    def energy_saving_mode(self):
        mode = lookup_enum("SmartSavingMode", self.data, self.refrigerator)
        return SmartSavingMode(mode)

    @property
    def door_opened(self):
        state = lookup_enum("DoorOpenState", self.data, self.refrigerator)
        return state == "OPEN"

    @property
    def temp_unit(self):
        return lookup_enum("TempUnit", self.data, self.refrigerator)

    @property
    def energy_saving_enabled(self):
        mode = lookup_enum(
            "SmartSavingModeStatus", self.data, self.refrigerator
        )
        return mode == "ON"

    @property
    def locked(self):
        status = lookup_enum("LockingStatus", self.data, self.refrigerator)
        return status == "LOCK"

    @property
    def active_saving_status(self):
        return self.data["ActiveSavingStatus"]

    @property
    def eco_enabled(self):
        eco = lookup_enum("EcoFriendly", self.data, self.refrigerator)
        return eco == "@CP_ON_EN_W"

    @property
    def water_filter_used_month(self):
        return self.data["WaterFilterUsedMonth"]
