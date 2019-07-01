import enum

from .client import Device


class DryerState(enum.Enum):
    """The state of the dryer device."""

    OFF = "@WM_STATE_POWER_OFF_W"
    INITIAL = "@WM_STATE_INITIAL_W"
    RUNNING = "@WM_STATE_RUNNING_W"
    DRYING = "@WM_STATE_DRYING_W"
    PAUSE = "@WM_STATE_PAUSE_W"
    END = "@WM_STATE_END_W"
    ERROR = "@WM_STATE_ERROR_W"
    COOLING = "@WM_STATE_COOLING_W"
    SMART_DIAGNOSIS = "@WM_STATE_SMART_DIAGNOSIS_W"
    WRINKLE_CARE = "@WM_STATE_WRINKLECARE_W"


class DryLevel(enum.Enum):
    """Represents the dry level setting of the dryer."""

    IRON = "@WM_DRY27_DRY_LEVEL_IRON_W"
    CUPBOARD = "@WM_DRY27_DRY_LEVEL_CUPBOARD_W"
    EXTRA = "@WM_DRY27_DRY_LEVEL_EXTRA_W"
    OFF = "-"
    DAMP = "@WM_DRY27_DRY_LEVEL_DAMP_W"
    LESS = "@WM_DRY27_DRY_LEVEL_LESS_W"
    NORMAL = "@WM_DRY27_DRY_LEVEL_NORMAL_W"
    MORE = "@WM_DRY27_DRY_LEVEL_MORE_W"
    VERY = "@WM_DRY27_DRY_LEVEL_VERY_W"


class DryerError(enum.Enum):
    """A dryer error."""

    ERROR_DOOR = "@WM_US_DRYER_ERROR_DE_W"
    ERROR_DRAINMOTOR = "@WM_US_DRYER_ERROR_OE_W"
    ERROR_LE1 = "@WM_US_DRYER_ERROR_LE1_W"
    ERROR_TE1 = "@WM_US_DRYER_ERROR_TE1_W"
    ERROR_TE2 = "@WM_US_DRYER_ERROR_TE2_W"
    ERROR_TE5 = "@WM_US_DRYER_ERROR_TE5_W"
    ERROR_TE6 = "@WM_US_DRYER_ERROR_TE6_W"
    ERROR_PS = "@WM_US_DRYER_ERROR_PS_W"
    ERROR_NP = "@WM_US_DRYER_ERROR_NP_GAS_W"
    ERROR_F1 = "@WM_US_DRYER_ERROR_F1_W"
    ERROR_LE2 = "@WM_US_DRYER_ERROR_LE2_W"
    ERROR_AE = "@WM_US_DRYER_ERROR_AE_W"
    ERROR_dE4 = "@WM_WW_FL_ERROR_DE4_W"
    ERROR_NOFILTER = "@WM_US_DRYER_ERROR_NOFILTER_W"
    ERROR_EMPTYWATER = "@WM_US_DRYER_ERROR_EMPTYWATER_W"
    ERROR_CE1 = "@WM_US_DRYER_ERROR_CE1_W"


class DryerDevice(Device):
    """A higher-level interface for a dryer."""

    def poll(self) -> Optional['DryerDevice']:
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`.

        :returns: Either a `DruerStatus` instance or `None` if the status is not
            yet available.
        """
        # Abort if monitoring has not started yet.
        if not hasattr(self, 'mon'):
            return None

        res = self.mon.poll_json()
        if res:
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

    @property
    def state(self):
        """Get the state of the dryer."""
        attr = 'State'
        return DryerState(self.dryer.model.enum_name(attr, self.data[attr]))

    @property
    def pre_state(self):
        """Get the previous? state of the dryer.


        @TODO: Run some tests to determine what this value means.  Is it the
        previous state?  If not, what would a pre-state mean?
        """
        attr = 'PreState'
        return DryerState(self.dryer.model.enum_name(attr, self.data[attr]))

    @property
    def dry_level(self):
        """Get the dry level."""
        attr = 'DryLevel'
        return DryLevel(self.dryer.model.enum_name(attr, self.data[attr]))

    @property
    def is_on(self) -> bool:
        """Check if the dryer is on or not."""
        return self.state != DryerState.OFF

    @property
    def remain_time_hours(self):
        """Get the remaining number of hours."""
        return self.data['Remain_Time_H']

    @property
    def remain_time_minutes(self):
        """Get the remaining number of minutes."""
        return self.data['Remain_Time_M']

    @property
    def initial_time_hours(self):
        """Get the initial number of hours."""
        return self.data['Initial_Time_H']

    @property
    def initial_time_minutes(self):
        """Get the initial number of minutes."""
        return self.data['Initial_Time_M']

    @property
    def course(self):
        """Get the current course."""
        raise NotImplementedError

    @property
    def smart_course(self):
        """Get the current smart course."""
        raise NotImplementedError
