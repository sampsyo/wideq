"""A `Device` class representing air conditioning/climate devices.
"""
import enum

from .client import Device, Monitor


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


class ACFanSpeed(enum.Enum):
    """The fan speed for an AC/HVAC device."""

    SLOW = '@AC_MAIN_WIND_STRENGTH_SLOW_W'
    SLOW_LOW = '@AC_MAIN_WIND_STRENGTH_SLOW_LOW_W'
    LOW = '@AC_MAIN_WIND_STRENGTH_LOW_W'
    LOW_MID = '@AC_MAIN_WIND_STRENGTH_LOW_MID_W'
    MID = '@AC_MAIN_WIND_STRENGTH_MID_W'
    MID_HIGH = '@AC_MAIN_WIND_STRENGTH_MID_HIGH_W'
    HIGH = '@AC_MAIN_WIND_STRENGTH_HIGH_W'
    POWER = '@AC_MAIN_WIND_STRENGTH_POWER_W'
    AUTO = '@AC_MAIN_WIND_STRENGTH_AUTO_W'


class ACOp(enum.Enum):
    """Whether a device is on or off."""

    OFF = "@AC_MAIN_OPERATION_OFF_W"
    RIGHT_ON = "@AC_MAIN_OPERATION_RIGHT_ON_W"  # This one seems to mean "on"?
    LEFT_ON = "@AC_MAIN_OPERATION_LEFT_ON_W"
    ALL_ON = "@AC_MAIN_OPERATION_ALL_ON_W"


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

        mapping = self.model.value('TempFahToCel').options
        return {int(f): c for f, c in mapping.items()}

    @property
    def c2f(self):
        """Get an inverse mapping from Celsius to Fahrenheit.

        Just as unbelievably, this is not exactly the inverse of the
        `f2c` map. There are a few values in this reverse mapping that
        are not in the other.
        """

        mapping = self.model.value('TempCelToFah').options
        out = {}
        for c, f in mapping.items():
            try:
                c_num = int(c)
            except ValueError:
                c_num = float(c)
            out[c_num] = f
        return out

    def set_celsius(self, c):
        """Set the device's target temperature in Celsius degrees.
        """

        self._set_control('TempCfg', c)

    def set_fahrenheit(self, f):
        """Set the device's target temperature in Fahrenheit degrees.
        """

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
        on_count = sum(int(zone['State']) for zone in zones)
        if on_count > 0:
            zone_cmd = '/'.join(
                '{}_{}'.format(zone['No'], zone['State'])
                for zone in zones if zone['Cfg'] == '1'
            )
            self._set_control('DuctZone', zone_cmd)

    def get_zones(self):
        """Get the status of the zones, including whether a zone is
        configured.

        The result is a list of dicts with the same format as described in
        `set_zones`.
        """

        return self._get_config('DuctZone')

    def set_fan_speed(self, speed):
        """Set the fan speed to a value from the `ACFanSpeed` enum.
        """

        speed_value = self.model.enum_value('WindStrength', speed.value)
        self._set_control('WindStrength', speed_value)

    def set_mode(self, mode):
        """Set the device's operating mode to an `OpMode` value.
        """

        mode_value = self.model.enum_value('OpMode', mode.value)
        self._set_control('OpMode', mode_value)

    def set_on(self, is_on):
        """Turn on or off the device (according to a boolean).
        """

        op = ACOp.RIGHT_ON if is_on else ACOp.OFF
        op_value = self.model.enum_value('Operation', op.value)
        self._set_control('Operation', op_value)

    def get_filter_state(self):
        """Get information about the filter."""

        return self._get_config('Filter')

    def get_mfilter_state(self):
        """Get information about the "MFilter" (not sure what this is).
        """

        return self._get_config('MFilter')

    def get_energy_target(self):
        """Get the configured energy target data."""

        return self._get_config('EnergyDesiredValue')

    def get_light(self):
        """Get a Boolean indicating whether the display light is on."""

        value = self._get_control('DisplayControl')
        return value == '0'  # Seems backwards, but isn't.

    def get_volume(self):
        """Get the speaker volume level."""

        value = self._get_control('SpkVolume')
        return int(value)

    def monitor_start(self):
        """Start monitoring the device's status."""

        mon = Monitor(self.client.session, self.device.id)
        mon.start()
        self.mon = mon

    def monitor_stop(self):
        """Stop monitoring the device's status."""

        self.mon.stop()

    def poll(self):
        """Poll the device's current state.

        Monitoring must be started first with `monitor_start`. Return
        either an `ACStatus` object or `None` if the status is not yet
        available.
        """

        # Abort if monitoring has not started yet.
        if not hasattr(self, 'mon'):
            return None

        res = self.mon.poll_json()
        if res:
            return ACStatus(self, res)
        else:
            return None


class ACStatus(object):
    """Higher-level information about an AC device's current status.
    """

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
        return self._str_to_num(self.data['TempCur'])

    @property
    def temp_cur_f(self):
        return self.ac.c2f[self.temp_cur_c]

    @property
    def temp_cfg_c(self):
        return self._str_to_num(self.data['TempCfg'])

    @property
    def temp_cfg_f(self):
        return self.ac.c2f[self.temp_cfg_c]

    def lookup_enum(self, key):
        return self.ac.model.enum_name(key, self.data[key])

    @property
    def mode(self):
        return ACMode(self.lookup_enum('OpMode'))

    @property
    def fan_speed(self):
        return ACFanSpeed(self.lookup_enum('WindStrength'))

    @property
    def is_on(self):
        op = ACOp(self.lookup_enum('Operation'))
        return op != ACOp.OFF
