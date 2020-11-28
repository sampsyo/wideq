import enum
from typing import Optional

from .client import Device
from .util import lookup_enum, lookup_reference


class WasherState(enum.Enum):
    """The state of the washer device."""

    ADD_DRAIN = "@WM_STATE_ADD_DRAIN_W"
    COMPLETE = "@WM_STATE_COMPLETE_W"
    DETECTING = "@WM_STATE_DETECTING_W"
    DETERGENT_AMOUNT = "@WM_STATE_DETERGENT_AMOUNT_W"
    DRYING = "@WM_STATE_DRYING_W"
    END = "@WM_STATE_END_W"
    ERROR_AUTO_OFF = "@WM_STATE_ERROR_AUTO_OFF_W"
    FRESH_CARE = "@WM_STATE_FRESHCARE_W"
    FROZEN_PREVENT_INITIAL = "@WM_STATE_FROZEN_PREVENT_INITIAL_W"
    FROZEN_PREVENT_PAUSE = "@WM_STATE_FROZEN_PREVENT_PAUSE_W"
    FROZEN_PREVENT_RUNNING = "@WM_STATE_FROZEN_PREVENT_RUNNING_W"
    INITIAL = "@WM_STATE_INITIAL_W"
    OFF = "@WM_STATE_POWER_OFF_W"
    PAUSE = "@WM_STATE_PAUSE_W"
    PRE_WASH = "@WM_STATE_PREWASH_W"
    RESERVE = "@WM_STATE_RESERVE_W"
    RINSING = "@WM_STATE_RINSING_W"
    RINSE_HOLD = "@WM_STATE_RINSE_HOLD_W"
    RUNNING = "@WM_STATE_RUNNING_W"
    SMART_DIAGNOSIS = "@WM_STATE_SMART_DIAG_W"
    SMART_DIAGNOSIS_DATA = "@WM_STATE_SMART_DIAGDATA_W"
    SPINNING = "@WM_STATE_SPINNING_W"
    TCL_ALARM_NORMAL = "TCL_ALARM_NORMAL"
    TUBCLEAN_COUNT_ALARM = "@WM_STATE_TUBCLEAN_COUNT_ALRAM_W"


class WasherDevice(Device):
    """A higher-level interface for a washer."""

    def poll(self) -> Optional["WasherStatus"]:
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`.

        :returns: Either a `WasherStatus` instance or `None` if the status is
            not yet available.
        """
        # Abort if monitoring has not started yet.
        if not hasattr(self, "mon"):
            return None

        data = self.mon.poll()
        if data:
            res = self.model.decode_monitor(data)
            return WasherStatus(self, res)
        else:
            return None


class WasherStatus(object):
    """Higher-level information about a washer's current status.

    :param washer: The WasherDevice instance.
    :param data: JSON data from the API.
    """

    def __init__(self, washer: WasherDevice, data: dict):
        self.washer = washer
        self.data = data

    @property
    def state(self) -> WasherState:
        """Get the state of the washer."""
        return WasherState(lookup_enum("State", self.data, self.washer))

    @property
    def previous_state(self) -> WasherState:
        """Get the previous state of the washer."""
        return WasherState(lookup_enum("PreState", self.data, self.washer))

    @property
    def is_on(self) -> bool:
        """Check if the washer is on or not."""
        return self.state != WasherState.OFF

    @property
    def remaining_time(self) -> int:
        """Get the remaining time in minutes."""
        return int(self.data["Remain_Time_H"]) * 60 + int(
            self.data["Remain_Time_M"]
        )

    @property
    def initial_time(self) -> int:
        """Get the initial time in minutes."""
        return int(self.data["Initial_Time_H"]) * 60 + int(
            self.data["Initial_Time_M"]
        )

    def _lookup_reference(self, attr: str) -> str:
        """Look up a reference value for the provided attribute.

        :param attr: The attribute to find the value for.
        :returns: The looked up value.
        """
        value = self.washer.model.reference_name(attr, self.data[attr])
        if value is None:
            return "Off"
        return value

    @property
    def course(self) -> str:
        """Get the current course."""
        return lookup_reference("APCourse", self.data, self.washer)

    @property
    def smart_course(self) -> str:
        """Get the current smart course."""
        return lookup_reference("SmartCourse", self.data, self.washer)

    @property
    def error(self) -> str:
        """Get the current error."""
        return lookup_reference("Error", self.data, self.washer)
