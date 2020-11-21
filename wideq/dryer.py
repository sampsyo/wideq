import enum
from typing import Optional

from .client import Device, _UNKNOWN
from .util import lookup_enum, lookup_reference


class DryerState(enum.Enum):
    """The state of the dryer device."""

    COOLING = "@WM_STATE_COOLING_W"
    END = "@WM_STATE_END_W"
    ERROR = "@WM_STATE_ERROR_W"
    DRYING = "@WM_STATE_DRYING_W"
    INITIAL = "@WM_STATE_INITIAL_W"
    OFF = "@WM_STATE_POWER_OFF_W"
    PAUSE = "@WM_STATE_PAUSE_W"
    RUNNING = "@WM_STATE_RUNNING_W"
    SMART_DIAGNOSIS = "@WM_STATE_SMART_DIAGNOSIS_W"
    WRINKLE_CARE = "@WM_STATE_WRINKLECARE_W"
    UNKNOWN = _UNKNOWN


class DryLevel(enum.Enum):
    """Represents the dry level setting of the dryer."""

    CUPBOARD = "@WM_DRY27_DRY_LEVEL_CUPBOARD_W"
    DAMP = "@WM_DRY27_DRY_LEVEL_DAMP_W"
    EXTRA = "@WM_DRY27_DRY_LEVEL_EXTRA_W"
    IRON = "@WM_DRY27_DRY_LEVEL_IRON_W"
    LESS = "@WM_DRY27_DRY_LEVEL_LESS_W"
    MORE = "@WM_DRY27_DRY_LEVEL_MORE_W"
    NORMAL = "@WM_DRY27_DRY_LEVEL_NORMAL_W"
    OFF = "-"
    VERY = "@WM_DRY27_DRY_LEVEL_VERY_W"
    UNKNOWN = _UNKNOWN


class DryerError(enum.Enum):
    """A dryer error."""

    ERROR_AE = "@WM_US_DRYER_ERROR_AE_W"
    ERROR_CE1 = "@WM_US_DRYER_ERROR_CE1_W"
    ERROR_DE4 = "@WM_WW_FL_ERROR_DE4_W"
    ERROR_DOOR = "@WM_US_DRYER_ERROR_DE_W"
    ERROR_DRAINMOTOR = "@WM_US_DRYER_ERROR_OE_W"
    ERROR_EMPTYWATER = "@WM_US_DRYER_ERROR_EMPTYWATER_W"
    ERROR_F1 = "@WM_US_DRYER_ERROR_F1_W"
    ERROR_LE1 = "@WM_US_DRYER_ERROR_LE1_W"
    ERROR_LE2 = "@WM_US_DRYER_ERROR_LE2_W"
    ERROR_NOFILTER = "@WM_US_DRYER_ERROR_NOFILTER_W"
    ERROR_NP = "@WM_US_DRYER_ERROR_NP_GAS_W"
    ERROR_PS = "@WM_US_DRYER_ERROR_PS_W"
    ERROR_TE1 = "@WM_US_DRYER_ERROR_TE1_W"
    ERROR_TE2 = "@WM_US_DRYER_ERROR_TE2_W"
    ERROR_TE5 = "@WM_US_DRYER_ERROR_TE5_W"
    ERROR_TE6 = "@WM_US_DRYER_ERROR_TE6_W"
    UNKNOWN = _UNKNOWN


class TempControl(enum.Enum):
    """Represents temperature control setting."""

    OFF = "-"
    ULTRA_LOW = "@WM_DRY27_TEMP_ULTRA_LOW_W"
    LOW = "@WM_DRY27_TEMP_LOW_W"
    MEDIUM = "@WM_DRY27_TEMP_MEDIUM_W"
    MID_HIGH = "@WM_DRY27_TEMP_MID_HIGH_W"
    HIGH = "@WM_DRY27_TEMP_HIGH_W"
    UNKNOWN = _UNKNOWN


class TimeDry(enum.Enum):
    """Represents a timed dry setting."""

    OFF = "-"
    TWENTY = "20"
    THIRTY = "30"
    FOURTY = "40"
    FIFTY = "50"
    SIXTY = "60"
    UNKNOWN = _UNKNOWN


class DryerDevice(Device):
    """A higher-level interface for a dryer."""

    def poll(self) -> Optional["DryerStatus"]:
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`.

        :returns: Either a `DryerStatus` instance or `None` if the status is
            not yet available.
        """
        # Abort if monitoring has not started yet.
        if not hasattr(self, "mon"):
            return None

        data = self.mon.poll()
        if data:
            res = self.model.decode_monitor(data)
            return DryerStatus(self, res)
        else:
            return None


class DryerStatus(object):
    """Higher-level information about a dryer's current status.

    :param dryer: The DryerDevice instance.
    :param data: JSON data from the API.
    """

    def __init__(self, dryer: DryerDevice, data: dict):
        self.dryer = dryer
        self.data = data

    def get_bit(self, key: str, index: int) -> str:
        bit_value = int(self.data[key])
        bit_index = 2 ** index
        mode = bin(bit_value & bit_index)
        if mode == bin(0):
            return "OFF"
        else:
            return "ON"

    @property
    def state(self) -> DryerState:
        """Get the state of the dryer."""
        return DryerState(lookup_enum("State", self.data, self.dryer))

    @property
    def previous_state(self) -> DryerState:
        """Get the previous state of the dryer."""
        return DryerState(lookup_enum("PreState", self.data, self.dryer))

    @property
    def dry_level(self) -> DryLevel:
        """Get the dry level."""
        return DryLevel(lookup_enum("DryLevel", self.data, self.dryer))

    @property
    def temperature_control(self) -> TempControl:
        """Get the temperature control setting."""
        return TempControl(lookup_enum("TempControl", self.data, self.dryer))

    @property
    def time_dry(self) -> TimeDry:
        """Get the time dry setting."""
        return TimeDry(lookup_enum("TimeDry", self.data, self.dryer))

    @property
    def is_on(self) -> bool:
        """Check if the dryer is on or not."""
        return self.state != DryerState.OFF

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

    @property
    def course(self) -> str:
        """Get the current course."""
        return lookup_reference("Course", self.data, self.dryer)

    @property
    def smart_course(self) -> str:
        """Get the current smart course."""
        return lookup_reference("SmartCourse", self.data, self.dryer)

    @property
    def error(self) -> str:
        """Get the current error."""
        return lookup_reference("Error", self.data, self.dryer)
