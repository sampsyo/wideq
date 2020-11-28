"""A `Device` class representing air conditioning/climate devices.
"""
import enum

from .client import Device
from .util import lookup_enum
from .core import FailedRequestError, InvalidRequestError


class ACJetMode(enum.Enum):
    """JET mode puts your AC into highest cooling or dry or
    heat mode(for a certain amount of time) depending on what you choose

    This mode Overrides following setting:
    1. Vertical swing is set to @100
    2. Temperature gets set to 18 after jet mode turns off
    3. Fan speed is set to HIGH (@AC_MAIN_WIND_STRENGTH_HIGH_W)
    after jet mode turns off
    """

    OFF = "@OFF"
    COOL = "@COOL_JET"
    HEAT = "@HEAT_JET"
    DRY = "@DRY_JET_W"
    HIMALAYAS = "@HIMALAYAS_COOL"


class ACVSwingMode(enum.Enum):
    """The vertical swing mode for an AC/HVAC device.

    Blades are numbered vertically from 1 (topmost)
    to 6.

    All is 100.
    """

    OFF = "@OFF"
    ONE = "@1"
    TWO = "@2"
    THREE = "@3"
    FOUR = "@4"
    FIVE = "@5"
    SIX = "@6"
    ALL = "@100"


class ACHSwingMode(enum.Enum):
    """The horizontal swing mode for an AC/HVAC device.

    Blades are numbered horizontally from 1 (leftmost)
    to 5.

    Left half goes from 1-3, and right half goes from
    3-5.

    All is 100.
    """

    OFF = "@OFF"
    ONE = "@1"
    TWO = "@2"
    THREE = "@3"
    FOUR = "@4"
    FIVE = "@5"
    LEFT_HALF = "@13"
    RIGHT_HALF = "@35"
    ALL = "@100"


class ACMode(enum.Enum):
    """The operation mode for an AC/HVAC device."""

    COOL = "@AC_MAIN_OPERATION_MODE_COOL_W"
    DRY = "@AC_MAIN_OPERATION_MODE_DRY_W"
    FAN = "@AC_MAIN_OPERATION_MODE_FAN_W"
    AI = "@AC_MAIN_OPERATION_MODE_AI_W"
    HEAT = "@AC_MAIN_OPERATION_MODE_HEAT_W"
    AIRCLEAN = "@AC_MAIN_OPERATION_MODE_AIRCLEAN_W"
    ACO = "@AC_MAIN_OPERATION_MODE_ACO_W"
    AROMA = "@AC_MAIN_OPERATION_MODE_AROMA_W"
    ENERGY_SAVING = "@AC_MAIN_OPERATION_MODE_ENERGY_SAVING_W"
    ENERGY_SAVER = "@AC_MAIN_OPERATION_MODE_ENERGY_SAVER_W"


class ACFanSpeed(enum.Enum):
    """The fan speed for an AC/HVAC device."""

    SLOW = "@AC_MAIN_WIND_STRENGTH_SLOW_W"
    SLOW_LOW = "@AC_MAIN_WIND_STRENGTH_SLOW_LOW_W"
    LOW = "@AC_MAIN_WIND_STRENGTH_LOW_W"
    LOW_MID = "@AC_MAIN_WIND_STRENGTH_LOW_MID_W"
    MID = "@AC_MAIN_WIND_STRENGTH_MID_W"
    MID_HIGH = "@AC_MAIN_WIND_STRENGTH_MID_HIGH_W"
    HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_W"
    POWER = "@AC_MAIN_WIND_STRENGTH_POWER_W"
    AUTO = "@AC_MAIN_WIND_STRENGTH_AUTO_W"
    NATURE = "@AC_MAIN_WIND_STRENGTH_NATURE_W"
    R_LOW = "@AC_MAIN_WIND_STRENGTH_LOW_RIGHT_W"
    R_MID = "@AC_MAIN_WIND_STRENGTH_MID_RIGHT_W"
    R_HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_RIGHT_W"
    L_LOW = "@AC_MAIN_WIND_STRENGTH_LOW_LEFT_W"
    L_MID = "@AC_MAIN_WIND_STRENGTH_MID_LEFT_W"
    L_HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_LEFT_W"
    L_LOWR_LOW = (
        "@AC_MAIN_WIND_STRENGTH_LOW_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_LOW_RIGHT_W"
    )
    L_LOWR_MID = (
        "@AC_MAIN_WIND_STRENGTH_LOW_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_MID_RIGHT_W"
    )
    L_LOWR_HIGH = (
        "@AC_MAIN_WIND_STRENGTH_LOW_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_HIGH_RIGHT_W"
    )
    L_MIDR_LOW = (
        "@AC_MAIN_WIND_STRENGTH_MID_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_LOW_RIGHT_W"
    )
    L_MIDR_MID = (
        "@AC_MAIN_WIND_STRENGTH_MID_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_MID_RIGHT_W"
    )
    L_MIDR_HIGH = (
        "@AC_MAIN_WIND_STRENGTH_MID_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_HIGH_RIGHT_W"
    )
    L_HIGHR_LOW = (
        "@AC_MAIN_WIND_STRENGTH_HIGH_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_LOW_RIGHT_W"
    )
    L_HIGHR_MID = (
        "@AC_MAIN_WIND_STRENGTH_HIGH_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_MID_RIGHT_W"
    )
    L_HIGHR_HIGH = (
        "@AC_MAIN_WIND_STRENGTH_HIGH_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_HIGH_RIGHT_W"
    )
    AUTO_2 = (
        "@AC_MAIN_WIND_STRENGTH_AUTO_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_AUTO_RIGHT_W"
    )
    POWER_2 = (
        "@AC_MAIN_WIND_STRENGTH_POWER_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_POWER_RIGHT_W"
    )
    LONGPOWER = (
        "@AC_MAIN_WIND_STRENGTH_LONGPOWER_LEFT_W|"
        "AC_MAIN_WIND_STRENGTH_LONGPOWER_RIGHT_W"
    )


class ACOp(enum.Enum):
    """Whether a device is on or off."""

    OFF = "@AC_MAIN_OPERATION_OFF_W"
    RIGHT_ON = "@AC_MAIN_OPERATION_RIGHT_ON_W"  # Right fan only.
    LEFT_ON = "@AC_MAIN_OPERATION_LEFT_ON_W"  # Left fan only.
    ALL_ON = "@AC_MAIN_OPERATION_ALL_ON_W"  # Both fans (or only fan) on.


class ACDevice(Device):
    """Higher-level operations on an AC/HVAC device, such as a heat
    pump.
    """

    @property
    def f2c(self):
        """Get a dictionary mapping Fahrenheit to Celsius temperatures for
        this device.

        Unbelievably, SmartThinQ devices have their own lookup tables
        for mapping the two temperature scales. You can get *close* by
        using a real conversion between the two temperature scales, but
        precise control requires using the custom LUT.
        """

        mapping = self.model.value("TempFahToCel").options
        return {int(f): c for f, c in mapping.items()}

    @property
    def c2f(self):
        """Get an inverse mapping from Celsius to Fahrenheit.

        Just as unbelievably, this is not exactly the inverse of the
        `f2c` map. There are a few values in this reverse mapping that
        are not in the other.
        """

        mapping = self.model.value("TempCelToFah").options
        out = {}
        for c, f in mapping.items():
            try:
                c_num = int(c)
            except ValueError:
                c_num = float(c)
            out[c_num] = f
        return out

    @property
    def supported_operations(self):
        """Get a list of the ACOp Operations the device supports."""

        mapping = self.model.value("Operation").options
        return [ACOp(o) for i, o in mapping.items()]

    @property
    def supported_on_operation(self):
        """Get the most correct "On" operation the device supports.
        :raises ValueError: If ALL_ON is not supported, but there are
            multiple supported ON operations. If a model raises this,
            its behaviour needs to be determined so this function can
            make a better decision.
        """

        operations = self.supported_operations
        operations.remove(ACOp.OFF)

        # This ON operation appears to be supported in newer AC models
        if ACOp.ALL_ON in operations:
            return ACOp.ALL_ON

        # Older models, or possibly just the LP1419IVSM, do not support ALL_ON,
        # instead advertising only a single operation of RIGHT_ON.
        # Thus, if there's only one ON operation, we use that.
        if len(operations) == 1:
            return operations[0]

        # Hypothetically, the API could return multiple ON operations, neither
        # of which are ALL_ON. This will raise in that case, as we don't know
        # what that model will expect us to do to turn everything on.
        # Or, this code will never actually be reached! We can only hope. :)
        raise ValueError(
            f"could not determine correct 'on' operation:"
            f" too many reported operations: '{str(operations)}'"
        )

    def set_celsius(self, c):
        """Set the device's target temperature in Celsius degrees."""

        self._set_control("TempCfg", c)

    def set_fahrenheit(self, f):
        """Set the device's target temperature in Fahrenheit degrees."""

        self.set_celsius(self.f2c[f])

    def set_zones(self, zones):
        """Turn off or on the device's zones.

        The `zones` parameter is a list of dicts with these keys:
        - "No": The zone index. A string containing a number,
          starting from 1.
        - "Cfg": Whether the zone is enabled. A string, either "1" or
          "0".
        - "State": Whether the zone is open. Also "1" or "0".
        """

        # Ensure at least one zone is enabled: we can't turn all zones
        # off simultaneously.
        on_count = sum(int(zone["State"]) for zone in zones)
        if on_count > 0:
            zone_cmd = "/".join(
                "{}_{}".format(zone["No"], zone["State"])
                for zone in zones
                if zone["Cfg"] == "1"
            )
            self._set_control("DuctZone", zone_cmd)

    def get_zones(self):
        """Get the status of the zones, including whether a zone is
        configured.

        The result is a list of dicts with the same format as described in
        `set_zones`.
        """

        return self._get_config("DuctZone")

    def set_jet_mode(self, jet_opt):
        """Set jet mode to a value from the `ACJetMode` enum."""

        jet_opt_value = self.model.enum_value("Jet", jet_opt.value)
        self._set_control("Jet", jet_opt_value)

    def set_fan_speed(self, speed):
        """Set the fan speed to a value from the `ACFanSpeed` enum."""

        speed_value = self.model.enum_value("WindStrength", speed.value)
        self._set_control("WindStrength", speed_value)

    def set_horz_swing(self, swing):
        """Set the horizontal swing to a value from the `ACHSwingMode` enum."""

        swing_value = self.model.enum_value("WDirHStep", swing.value)
        self._set_control("WDirHStep", swing_value)

    def set_vert_swing(self, swing):
        """Set the vertical swing to a value from the `ACVSwingMode` enum."""

        swing_value = self.model.enum_value("WDirVStep", swing.value)
        self._set_control("WDirVStep", swing_value)

    def set_mode(self, mode):
        """Set the device's operating mode to an `OpMode` value."""

        mode_value = self.model.enum_value("OpMode", mode.value)
        self._set_control("OpMode", mode_value)

    def set_on(self, is_on):
        """Turn on or off the device (according to a boolean)."""

        op = self.supported_on_operation if is_on else ACOp.OFF
        op_value = self.model.enum_value("Operation", op.value)
        self._set_control("Operation", op_value)

    def get_filter_state(self):
        """Get information about the filter."""

        return self._get_config("Filter")

    def get_mfilter_state(self):
        """Get information about the "MFilter" (not sure what this is)."""

        return self._get_config("MFilter")

    def get_energy_target(self):
        """Get the configured energy target data."""

        return self._get_config("EnergyDesiredValue")

    def get_outdoor_power(self):
        """Get instant power usage in watts of the outdoor unit"""

        try:
            value = self._get_config("OutTotalInstantPower")
            return value["OutTotalInstantPower"]
        except InvalidRequestError:
            # Device does not support outdoor unit instant power usage
            return 0

    def get_power(self):
        """Get the instant power usage in watts of the whole unit"""

        try:
            value = self._get_config("InOutInstantPower")
            return value["InOutInstantPower"]
        except InvalidRequestError:
            # Device does not support whole unit instant power usage
            return 0

    def get_light(self):
        """Get a Boolean indicating whether the display light is on."""

        try:
            value = self._get_control("DisplayControl")
            return value == "0"  # Seems backwards, but isn't.
        except FailedRequestError:
            # Device does not support reporting display light status.
            # Since it's probably not changeable the it must be on.
            return True

    def get_volume(self):
        """Get the speaker volume level."""

        try:
            value = self._get_control("SpkVolume")
            return int(value)
        except FailedRequestError:
            return 0  # Device does not support volume control.

    def poll(self):
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`. Return
        either an `ACStatus` object or `None` if the status is not yet
        available.
        """

        # Abort if monitoring has not started yet.
        if not hasattr(self, "mon"):
            return None

        res = self.mon.poll_json()
        if res:
            return ACStatus(self, res)
        else:
            return None


class ACStatus(object):
    """Higher-level information about an AC device's current status."""

    def __init__(self, ac, data):
        self.ac = ac
        self.data = data

    @staticmethod
    def _str_to_num(s):
        """Convert a string to either an `int` or a `float`.

        Troublingly, the API likes values like "18", without a trailing
        ".0", for whole numbers. So we use `int`s for integers and
        `float`s for non-whole numbers.
        """

        f = float(s)
        if f == int(f):
            return int(f)
        else:
            return f

    @property
    def temp_cur_c(self):
        return self._str_to_num(self.data["TempCur"])

    @property
    def temp_cur_f(self):
        return self.ac.c2f[self.temp_cur_c]

    @property
    def temp_cfg_c(self):
        return self._str_to_num(self.data["TempCfg"])

    @property
    def temp_cfg_f(self):
        return self.ac.c2f[self.temp_cfg_c]

    @property
    def mode(self):
        return ACMode(lookup_enum("OpMode", self.data, self.ac))

    @property
    def fan_speed(self):
        return ACFanSpeed(lookup_enum("WindStrength", self.data, self.ac))

    @property
    def horz_swing(self):
        return ACHSwingMode(lookup_enum("WDirHStep", self.data, self.ac))

    @property
    def vert_swing(self):
        return ACVSwingMode(lookup_enum("WDirVStep", self.data, self.ac))

    @property
    def is_on(self):
        op = ACOp(lookup_enum("Operation", self.data, self.ac))
        return op != ACOp.OFF

    def __str__(self):
        return "ACStatus(%r %r)" % (self.ac, self.data)
