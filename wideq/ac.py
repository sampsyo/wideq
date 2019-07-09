    
"""A `Device` class representing air conditioning/climate devices.
"""
import enum

from .client import Device


class ACMode(enum.Enum):
    """The operation mode for an AC/HVAC device."""

    OFF = "@OFF"
    NOT_SUPPORTED = "@NON"
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
    SMARTCARE = "@AC_MAIN_WIND_MODE_SMARTCARE_W"
    ICEVALLEY = "@AC_MAIN_WIND_MODE_ICEVALLEY_W"
    LONGPOWER = "@AC_MAIN_WIND_MODE_LONGPOWER_W"


class ACFanSpeed(enum.Enum):
    """The fan speed for an AC/HVAC device."""
    
    #for stand type or wall mount type
    NOT_SUPPORTED = "@NON"
    FIX = "@AC_MAIN_WIND_DIRECTION_FIX_W"
    LOW = "@AC_MAIN_WIND_STRENGTH_LOW_LEFT_W|AC_MAIN_WIND_STRENGTH_LOW_RIGHT_W"
    MID = "@AC_MAIN_WIND_STRENGTH_MID_LEFT_W|AC_MAIN_WIND_STRENGTH_MID_RIGHT_W"
    HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_LEFT_W|AC_MAIN_WIND_STRENGTH_HIGH_RIGHT_W"
    COOLPOWER = "@AC_MAIN_WIND_STRENGTH_POWER_LEFT_W|AC_MAIN_WIND_STRENGTH_POWER_RIGHT_W"
    LONGPOWER ="@AC_MAIN_WIND_STRENGTH_LONGPOWER_LEFT_W|AC_MAIN_WIND_STRENGTH_LONGPOWER_RIGHT_W"
    AUTO = "@AC_MAIN_WIND_STRENGTH_AUTO_LEFT_W|AC_MAIN_WIND_STRENGTH_AUTO_RIGHT_W"
    RIGHT_LOW_LEFT_MID = "@AC_MAIN_WIND_STRENGTH_MID_LEFT_W|AC_MAIN_WIND_STRENGTH_LOW_RIGHT_W"
    RIGHT_LOW_LEFT_HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_LEFT_W|AC_MAIN_WIND_STRENGTH_LOW_RIGHT_W"
    RIGHT_MID_LEFT_LOW = "@AC_MAIN_WIND_STRENGTH_LOW_LEFT_W|AC_MAIN_WIND_STRENGTH_MID_RIGHT_W"
    RIGHT_MID_LEFT_HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_LEFT_W|AC_MAIN_WIND_STRENGTH_MID_RIGHT_W"
    RIGHT_HIGH_LEFT_LOW = "@AC_MAIN_WIND_STRENGTH_LOW_LEFT_W|AC_MAIN_WIND_STRENGTH_HIGH_RIGHT_W"
    RIGHT_HIGH_LEFT_MID = "@AC_MAIN_WIND_STRENGTH_MID_LEFT_W|AC_MAIN_WIND_STRENGTH_HIGH_RIGHT_W"
    RIGHT_ONLY_LOW = "@AC_MAIN_WIND_STRENGTH_LOW_RIGHT_W"
    RIGHT_ONLY_MID = "@AC_MAIN_WIND_STRENGTH_MID_RIGHT_W"
    RIGHT_ONLY_HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_RIGHT_W"
    LEFT_ONLY_LOW = "@AC_MAIN_WIND_STRENGTH_LOW_LEFT_W"
    LEFT_ONLY_MID = "@AC_MAIN_WIND_STRENGTH_MID_LEFT_W"
    LEFT_ONLY_HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_LEFT_W"
    
    #for system type 
    SYSTEM_SLOW = "@AC_MAIN_WIND_STRENGTH_SLOW_W"
    SYSTEM_LOW = "@AC_MAIN_WIND_STRENGTH_LOW_W"
    SYSTEM_MID = "@AC_MAIN_WIND_STRENGTH_MID_W"
    SYSTEM_HIGH = "@AC_MAIN_WIND_STRENGTH_HIGH_W"
    SYSTEM_POWER = "@AC_MAIN_WIND_STRENGTH_POWER_W"
    SYSTEM_AUTO = "@AC_MAIN_WIND_STRENGTH_AUTO_W"
    SYSTEM_LOW_CLEAN = "@AC_MAIN_WIND_STRENGTH_LOW_CLEAN_W"
    SYSTEM_MID_CLEAN = "@AC_MAIN_WIND_STRENGTH_MID_CLEAN_W"
    SYSTEM_HIGH_CLEAN = "@AC_MAIN_WIND_STRENGTH_HIGH_CLEAN_W"

class ACOp(enum.Enum):
    """Whether a device is on or off."""
    
    OFF = "@AC_MAIN_OPERATION_OFF_W"
    RIGHT_ON = "@AC_MAIN_OPERATION_RIGHT_ON_W" #if device has one out duct, this is "on".
    LEFT_ON = "@AC_MAIN_OPERATION_LEFT_ON_W"
    ALL_ON = "@AC_MAIN_OPERATION_ALL_ON_W"

class ACSwingMode(enum.Enum):
    """The swingmode for an AC/HVAC device."""
    FIX = "@AC_MAIN_WIND_DIRECTION_FIX_W"
    UPDOWN = "@AC_MAIN_WIND_DIRECTION_UP_DOWN_W"
    LEFTRIGHT = "@AC_MAIN_WIND_DIRECTION_LEFT_RIGHT_W"

class ACReserveMode(enum.Enum):
    """The reserve mode for an AC/HVAC device."""
    NONE = "@NON"
    SLEEPTIMER = "@SLEEP_TIMER"
    EASYTIMER = "@EASY_TIMER"
    ONOFFTIMER = "@ONOFF_TIMER"
    TIMEBS = "@TIMEBS_ONOFF"
    WEEKLYSCHEDULE = "@WEEKLY_SCHEDULE"

class ACEXTRAMode(enum.Enum):
    """The extra mode for an AC/HVAC device."""
    NONE = "@NON"
    POWERSAVE = "@ENERGYSAVING"
    AUTODRY = "@AUTODRY"
    AIRCLEAN = "@AIRCLEAN"
    ECOMODE = "@ECOMODE"
    POWERSAVEDRY = "@ENERGYSAVINGDRY"
    INDIVIDUALCTRL = "@INDIVIDUALCTRL"
    COMBINATION_OF_COMMAND = "@COMBINATION_OF_COMMAND"  
    QUITE_MODE = "@QUITE_MODE"

class ACRACSubMode(enum.Enum):
    """The rac model sub mode for an AC/HVAC device."""
    NONE = "@NON"
    UP_DOWN = "@AC_MAIN_WIND_DIRECTION_SWING_UP_DOWN_W"
    LEFT_RIGHT = "@AC_MAIN_WIND_DIRECTION_SWING_LEFT_RIGHT_W"
    JET = "@AC_MAIN_WIND_MODE_JET_W"

class ACAirPolution(enum.Enum):
    """Check  AC/HVAC device support air polution function"""
    NONE = "@NON"
    MONITORING_SUPPORT = "@SENSOR_MONITORING_SET_SUPPORT"
    TOTALCLEAN_SUPPORT = "@TOTAL_CLEAN_SUPPORT"
    PM1_SUPPORT = "@PM1_0_SUPPORT"
    PM10_SUPPORT = "@PM10_SUPPORT"
    PM2_SUPPORT = "@PM2_5_SUPPORT"
    SENSOR_HUMID_SUPPORT = "@SENSOR_HUMID_SUPPORT"
    YELLOW_DUST_MON_SUPPORT = "@YELLOW_DUST_MON_SUPPORT"

class AIRCLEAN(enum.Enum):
    """ turn on/off air purifier mode"""

    OFF = "@AC_MAIN_AIRCLEAN_OFF_W"
    ON = "@AC_MAIN_AIRCLEAN_ON_W"

class WDIRLEFTRIGHT(enum.Enum):
    """The wind direction L/R for an AC/HVAC device."""

    LEFT_RIGHT_STOP = "@OFF"
    LEFT_RIGTH_ON = "@ON"
    RIGHTSIDE_LEFT_RIGHT = "@RIGHT_ON"  #this is for device which have two out duct.
    LEFTSIDE_LEFT_RIGHT = "@LEFT_ON"
    LEFT_RIGHT = "@ALL_ON"

class WDIRVSTEP(enum.Enum):
    """The wind vertical direction step control for an AC/HVAC device."""
    OFF = "0"
    FIRST = "1"
    SECOND = "2"
    THIRD = "3"
    FOURTH = "4"
    FIFTH = "5"
    SIXTH = "6"
    AUTO = "100"

class WDIRHSTEP(enum.Enum):
    """The wind horizontal direction step control for an AC/HVAC device."""

    OFF = "0"
    FIRST = "1"
    SECOND = "2"
    THIRD = "3"
    FOURTH = "4"
    FIFTH = "5"
    THIRTEENTH = "13"
    THIRTYFIFTH = "35"
    AUTO = "100"

class FOURVAIN_WDIRVSTEP(enum.Enum):
    """The four vain model(like system aircon) vertical direction step control for an AC/HVAC device."""

    OFF = "0"
    FIRST = "8737"
    SECOND = "8738"
    THIRD = "8739"
    FOURTH = "8740"
    FIFTH = "8741"
    SIXTH = "8742"


class ACETCMODE(enum.Enum):
    """for extra mode on/off"""
    OFF = "@OFF"
    ON = "@ON" 

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

        op = ACOp.ALL_ON if is_on else ACOp.OFF
        op_value = self.model.enum_value('Operation', op.value)
        self._set_control('Operation', op_value)

    def set_wind_leftright(self, mode):
        """Set the device's wind direction mode to an `WDirLeftRight` value.
        """
        
        wdir_value = self.model.enum_value('WDirLeftRight', mode.value)
        self._set_control('WDirLeftRight', wdir_value)

    def set_wdirhstep(self, mode):
        """Set the device's wind horizontal direction mode to an `WDirHStep` value.
        """

        self._set_control_ac_wdirstep('WDirHStep',int(mode.value))

    def set_wdirvstep(self, mode):
        """Set the device's wind vertical direction mode to an `WDirVStep` value.
        """

        self._set_control_ac_wdirstep('WDirVStep',int(mode.value))

    def set_airclean(self, is_on):
        """Set the device's air purifier mode to an `AirClean` value.
        """

        mode = AIRCLEAN.ON if is_on else AIRCLEAN.OFF
        mode_value = self.model.enum_value('AirClean', mode.value)
        self._set_control('AirClean', mode_value)

    def set_etc_mode(self, name, is_on):
        """Set the device's extra function mode to each value.
        """

        mode = ACETCMODE.ON if is_on else ACETCMODE.OFF
        mode_value = self.model.enum_value(name, mode.value)
        self._set_control(name, mode_value)

    def set_sleep_time(self, sleeptime):
       """Set the device's sleap timeer to an `SleepTime` value.
        """
        self._set_control('SleepTime', sleeptime)

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

    def get_outdoor_weather(self, area):
        """Get outdoor weather"""

        data = self.client.session.get_outdoor_weather(area)
        return data

    def get_dustsensor(self, device_id):
        """ get dust sensor value"""
        data = self.client.session.get_dustsensor_data(device_id)

    def get_energy_usage_day(self):
        """Get Energy usage for today"""
        sDate = datetime.today().strftime("%Y%m%d")
        eDate = sDate
        data = self._get_power_data(sDate, eDate)
        if data == '0':
            return data
        else:
            energy_data = data.split('_')
            energy = int(energy_data[2])
            return energy

    def get_usage_time_day(self):
        """Get ac using time for today"""
        sDate = datetime.today().strftime("%Y%m%d")
        eDate = sDate
        data = self._get_power_data(sDate, eDate)
        if data == '0':
            return data
        else: 
            time_data = data.split('_')
            time = int(energy_data[1])
            return time

    def get_energy_usage_week(self):
        """Get Energy usage for this week(sun to sat)"""

        weekday = datetime.today().weekday()

        startdate = datetime.today() + timedelta(days=-(weekday+1))
        enddate = datetime.today() + timedelta(days=(6-(weekday+1)))
        sDate = datetime.date(startdate).strftime("%Y%m%d")
        eDate = datetime.date(enddate).strftime("%Y%m%d")

        data = self._get_power_data(sDate, eDate)
        if data == '0':
            return data
        else:
            value = data.split('/')
            value_no = len(value)
            energy = []
            i = 0
            for i in range(0, value_no):
                energy_data = value[i].split('_')
                energy.append(int(energy_data[2]))
                i = i+1
            energy_sum = sum(energy)
            return energy_sum

    def get_usage_time_week(self):
        """Get ac using time for this week(sun to sat)"""

        weekday = datetime.today().weekday()

        startdate = datetime.today() + timedelta(days=-(weekday+1))
        enddate = datetime.today() + timedelta(days=(6-(weekday+1)))
        sDate = datetime.date(startdate).strftime("%Y%m%d")
        eDate = datetime.date(enddate).strftime("%Y%m%d")

        data = self._get_power_data(sDate, eDate)
        if data == '0':
            return data
        else:
            value = data.split('/')
            value_no = len(value)
            time = []
            i = 0
            for i in range(0, value_no):
                time_data = value[i].split('_')
                time.append(int(time_data[1]))
                i = i+1
            time_sum = sum(time)
            return time_sum     

    def get_energy_usage_month(self):
        """Get Energy usage for this month"""

        weekday = datetime.today().weekday()

        startdate = datetime.today().replace(day=1)
        sDate = datetime.date(startdate).strftime("%Y%m%d")
        eDate = datetime.today().strftime("%Y%m%d")
        
        data = self._get_power_data(sDate, eDate)
        if data == '0':
            return data
        else:
            value = data.split('/')
            value_no = len(value)
            energy = []
            i = 0
            for i in range(0, value_no):
                energy_data = value[i].split('_')
                energy.append(int(energy_data[2]))
                i = i+1
            energy_sum = sum(energy)
            return energy_sum

    def get_usage_time_month(self):
        """Get ac using time for this month"""

        weekday = datetime.today().weekday()

        startdate = datetime.today().replace(day=1)
        sDate = datetime.date(startdate).strftime("%Y%m%d")
        eDate = datetime.today().strftime("%Y%m%d")
        
        data = self._get_power_data(sDate, eDate)
        if data == '0':
            return data
        else:
            value = data.split('/')
            value_no = len(value)
            time = []
            i = 0
            for i in range(0, value_no):
                time_data = value[i].split('_')
                time.append(int(time_data[1]))
                i = i+1
            time_sum = sum(time)
            return time_sum

    def get_outtotalinstantpower(self):
        """Get Energy usage of outdoor unit"""

        value = self._get_config('OutTotalInstantPower')
        return value['OutTotalInstantPower']

    def get_inoutinstantpower(self):
        """Get Energy usage of total unit"""

        value = self._get_config('InOutInstantPower')
        return value['InOutInstantPower']

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
    def support_oplist(self):
        """ find device's support oplist"""
        dict_support_opmode = self.ac.model.option_item('SupportOpMode')
        support_opmode = []
        for option in dict_support_opmode.values():
            support_opmode.append(ACMode(option).name)
    
        return support_opmode

    @property
    def support_windmode(self):
        """ find device's support wind mode"""

        dict_support_windmode = self.ac.model.option_item('SupportWindMode')
        support_windmode = []
        for option in dict_support_windmode.values():
            support_windmode.append(ACMode(option).name)
    
        return support_windmode

    @property
    def support_fanlist(self):
        """ find device's support fan speed"""

        dict_support_fanmode = self.ac.model.option_item('SupportWindStrength')
        support_fanmode = []
        for option in dict_support_fanmode.values():
            support_fanmode.append(ACWindstrength(option).name)
    
        return support_fanmode

    @property
    def support_swingmode(self):
        """ find device's support wind direction"""

        dict_support_swingmode = self.ac.model.option_item('SupportWindDir')
        support_swingmode = []
        for option in dict_support_swingmode.values():
            support_swingmode.append(ACSwingMode(option).name)
    
        return support_swingmode

    @property
    def support_pacmode(self):
        """ find device's support pac model mode"""

        if self.ac.model.model_type == 'PAC':
            dict_support_pacmode = self.ac.model.option_item('SupportPACMode')
            support_pacmode = []
            for option in dict_support_pacmode.values():
                support_pacmode.append(ACEXTRAMode(option).name)
        
        return support_pacmode

    @property
    def support_racmode(self):
        """ find device's support rac model mode"""

        if self.ac.model.model_type == 'RAC':
            dict_support_racmode = self.ac.model.option_item('SupportRACMode')
            support_racmode = []
            for option in dict_support_racmode.values():
                support_racmode.append(ACEXTRAMode(option).name)
        
            return support_racmode
    
    @property
    def support_racsubmode(self):
        """ find device's support rac model submode"""

        if self.ac.model.model_type == 'RAC' or self.ac.model.model_type == 'SAC_CST':
            dict_support_racsubmode = self.ac.model.option_item('SupportRACSubMode')
            support_racsubmode = []
            for option in dict_support_racsubmode.values():
                support_racsubmode.append(ACRACSubMode(option).name)
        
            return support_racsubmode

    @property
    def support_reservemode(self):
        """ find device's support reserve mode"""

        dict_support_reservemode = self.ac.model.option_item('SupportReserve')
        support_reservemode = []
        for option in dict_support_reservemode.values():
            support_reservemode.append(ACReserveMode(option).name)
    
        return support_reservemode

    @property
    def support_airpolution(self):
        """ find device's support air polution mode"""

        dict_support_airpolution = self.ac.model.option_item('SupportAirPolution')
        support_airpolution = []
        for option in dict_support_airpolution.values():
            support_airpolution.append(ACAirPolution(option).name)
    
        return support_airpolution

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

    @property
    def wdirleftright_state(self):
        return WDIRLEFTRIGHT(self.lookup_enum('WDirLeftRight'))

    @property
    def wdirupdown_state(self):
        return ACETCMODE(self.lookup_enum('WDirUpDown'))    

    @property
    def airclean_state(self):
        return AIRCLEAN(self.lookup_enum('AirClean'))

    @property
    def wdirvstep_state(self):
        return WDIRVSTEP(self.data['WDirVStep'])

    @property
    def wdirhstep_state(self):
        return WDIRHSTEP(self.data['WDirHStep'])

    @property
    def fourvain_wdirvstep_state(self):
        return FOURVAIN_WDIRVSTEP(self.data['WDirVStep'])

    @property
    def sac_airclean_state(self):
        return ACETCMODE(self.lookup_enum('AirClean'))    
    
    @property
    def icevalley_state(self):
        return ACETCMODE(self.lookup_enum('IceValley'))
    
    @property
    def longpower_state(self):
        return ACETCMODE(self.lookup_enum('FlowLongPower'))
    
    @property
    def autodry_state(self):
        return ACETCMODE(self.lookup_enum('AutoDry'))
    
    @property
    def smartcare_state(self):
        return ACETCMODE(self.lookup_enum('SmartCare'))
    
    @property
    def sensormon_state(self):
        return ACETCMODE(self.lookup_enum('SensorMon'))
    
    @property
    def powersave_state(self):
        return ACETCMODE(self.lookup_enum('PowerSave'))

    @property
    def jet_state(self):
        return ACETCMODE(self.lookup_enum('Jet'))

    @property
    def humidity(self):
        return self.data['SensorHumidity']
    
    @property
    def sensorpm1(self):
        return self.data['SensorPM1']
    
    @property
    def sensorpm2(self):
        return self.data['SensorPM2']
    
    @property
    def sensorpm10(self):
        return self.data['SensorPM10']

    @property
    def sleeptime(self):
        return self.data['SleepTime']

    @property
    def total_air_polution(self):
        return APTOTALAIRPOLUTION(self.data['TotalAirPolution'])
    
    @property
    def air_polution(self):
        return APSMELL(self.data['AirPolution'])
