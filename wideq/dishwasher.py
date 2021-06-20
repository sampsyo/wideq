import enum
from typing import Optional

from .client import Device
from .util import lookup_enum, lookup_reference


class DishWasherState(enum.Enum):
    """The state of the dishwasher device."""

    INITIAL = "@DW_STATE_INITIAL_W"
    RUNNING = "@DW_STATE_RUNNING_W"
    PAUSED = "@DW_STATE_PAUSE_W"
    OFF = "@DW_STATE_POWER_OFF_W"
    COMPLETE = "@DW_STATE_COMPLETE_W"
    POWER_FAIL = "@DW_STATE_POWER_FAIL_W"


DISHWASHER_STATE_READABLE = {
    "INITIAL": "Standby",
    "RUNNING": "Running",
    "PAUSED": "Paused",
    "OFF": "Off",
    "COMPLETE": "Complete",
    "POWER_FAIL": "Power Failed",
}


class DishWasherProcess(enum.Enum):
    """The process within the dishwasher state."""

    RESERVE = "@DW_STATE_RESERVE_W"
    RUNNING = "@DW_STATE_RUNNING_W"
    RINSING = "@DW_STATE_RINSING_W"
    DRYING = "@DW_STATE_DRYING_W"
    COMPLETE = "@DW_STATE_COMPLETE_W"
    NIGHT_DRYING = "@DW_STATE_NIGHTDRY_W"
    CANCELLED = "@DW_STATE_CANCEL_W"


DISHWASHER_PROCESS_READABLE = {
    "RESERVE": "Delayed Start",
    "RUNNING": DISHWASHER_STATE_READABLE["RUNNING"],
    "RINSING": "Rinsing",
    "DRYING": "Drying",
    "COMPLETE": DISHWASHER_STATE_READABLE["COMPLETE"],
    "NIGHT_DRYING": "Night Drying",
    "CANCELLED": "Cancelled",
}


# Provide a map to correct typos in the official course names.
DISHWASHER_COURSE_MAP = {
    "Haeavy": "Heavy",
}


class DishWasherDevice(Device):
    """A higher-level interface for a dishwasher."""

    def poll(self) -> Optional["DishWasherStatus"]:
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`.

        :returns: Either a `DishWasherStatus` instance or `None` if the status
            is not yet available.
        """
        # Abort if monitoring has not started yet.
        if not hasattr(self, "mon"):
            return None

        data = self.mon.poll()
        if data:
            res = self.model.decode_monitor(data)
            return DishWasherStatus(self, res)
        else:
            return None


class DishWasherStatus(object):
    """Higher-level information about a dishwasher's current status.

    :param dishwasher: The DishWasherDevice instance.
    :param data: Binary data from the API.
    """

    def __init__(self, dishwasher: DishWasherDevice, data: dict):
        self.dishwasher = dishwasher
        self.data = data

    @property
    def state(self) -> DishWasherState:
        """Get the state of the dishwasher."""
        return DishWasherState(
            lookup_enum("State", self.data, self.dishwasher)
        )

    @property
    def readable_state(self) -> str:
        """Get a human readable state of the dishwasher."""
        return DISHWASHER_STATE_READABLE[self.state.name]

    @property
    def process(self) -> Optional[DishWasherProcess]:
        """Get the process of the dishwasher."""
        process = lookup_enum("Process", self.data, self.dishwasher)
        if process and process != "-":
            return DishWasherProcess(process)
        else:
            return None

    @property
    def readable_process(self) -> str:
        """Get a human readable process of the dishwasher."""
        if self.process:
            return DISHWASHER_PROCESS_READABLE[self.process.name]
        else:
            return ""

    @property
    def is_on(self) -> bool:
        """Check if the dishwasher is on or not."""
        return self.state != DishWasherState.OFF

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
    def reserve_time(self) -> int:
        """Get the reserve time in minutes."""
        return int(self.data["Reserve_Time_H"]) * 60 + int(
            self.data["Reserve_Time_M"]
        )

    @property
    def course(self) -> str:
        """Get the current course."""
        course = lookup_reference("Course", self.data, self.dishwasher)
        if course in DISHWASHER_COURSE_MAP:
            return DISHWASHER_COURSE_MAP[course]
        else:
            return course

    @property
    def smart_course(self) -> str:
        """Get the current smart course."""
        return lookup_reference("SmartCourse", self.data, self.dishwasher)

    @property
    def error(self) -> str:
        """Get the current error."""
        return lookup_reference("Error", self.data, self.dishwasher)
