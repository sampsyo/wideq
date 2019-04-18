import wideq
import json
import time
import sys

STATE_FILE = 'wideq_state.json'
   
def authenticate(gateway):
    """Interactively authenticate the user via a browser to get an OAuth
    session.
    """

    login_url = gateway.oauth_url()
    print('Log in here:')
    print(login_url)
    print('Then paste the URL where the browser is redirected:')
    callback_url = input()
    return wideq.Auth.from_url(gateway, callback_url)


def ls(client):
    """List the user's devices."""
    list = {}
    for device in client.devices:
        res = {
            'device_id':device.id,
            'device_type':device.type.name,
            'device_model':device.model_id,
            'device_macaddress':device.macaddress,
            }
        list['Device Name :'+device.name] = res

        print('device_name: ''{0.name}'.format(device),
              'device_id: ' '{0.id}'.format(device),
              'device_type: ''{0.type.name}'.format(device),
              'device_model: ' '{0.model_id}'.format(device),
              'device_macaddress: ' '{0.macaddress}'.format(device),
              sep='\n', end='\n\n')
                 
    # Save my device list
    with open('my_device_list.json', 'w',encoding="utf-8") as outfile:
         json.dump(list, outfile, ensure_ascii = False)
"""
def ls(client):

    for device in client.devices:
        print('{0.id}: {0.name} ({0.type.name} {0.model_id}) {0.macaddress}'.format(device))
"""

def mon(client, device_id):
    """Monitor any device, displaying generic information about its
    status.
    """

    device = client.get_device(device_id)
    model = client.model_info(device)

    with wideq.Monitor(client.session, device_id) as mon:
        try:
            while True:
                time.sleep(1)
                print('Polling...')
                data = mon.poll()
                if data:
                    try:
                        res = model.decode_monitor(data)
                    except ValueError:
                        print('status data: {!r}'.format(data))
                    else:
                        for key, value in res.items():
                            try:
                                desc = model.value(key)
                                if isinstance(desc, wideq.EnumValue):
                                    print('- {}: {}'.format(
                                        key, desc.options.get(value, value)
                                    ))
                                elif isinstance(desc, wideq.RangeValue):
                                    print('- {0}: {1} ({2.min}-{2.max})'.format(
                                        key, value, desc,
                                    ))
                            except KeyError:
                                print('- {}: {}'.format(key, value))

        except KeyboardInterrupt:
            pass

def getDeviceInfo(client, device_id):
    device = client.get_device(device_id)
    deviceName = device.name
    
    with open(deviceName + '_info.json', 'w') as outfile:
        json.dump(device.data, outfile, ensure_ascii = False)
    
    
def getModelInfo(client, device_id):
    device = client.get_device(device_id)
    model = client.model_info(device)
    modelName = model.data['Info']['modelName']
    
    with open(modelName + '_info.json', 'w') as outfile:
        json.dump(model.data, outfile, ensure_ascii = False)
        
def ac_mon(client, device_id):
    """Monitor an AC/HVAC device, showing higher-level information about
    its status such as its temperature and operation mode.
    """

    device = client.get_device(device_id)
    if device.type != wideq.DeviceType.AC:
        print('This is not an AC device.')
        return

    ac = wideq.ACDevice(client, device)

    try:
        ac.monitor_start()
        while True:
            time.sleep(1)
            state = ac.poll()
            if state:
                print(
                    '{1}; '
                    '{0.mode.name}; '
                    'cur {0.temp_cur_f} F; '
                    'cfg {0.temp_cfg_f} F; '
                    'air clean {0.airclean_state.name}'
                    .format(
                        state,
                        'on' if state.is_on else 'off'
                    )
                )

    except KeyboardInterrupt:
        pass
    finally:
        ac.monitor_stop()


def set_temp(client, device_id, temp):
    """Set the configured temperature for an AC device."""

    ac = wideq.ACDevice(client, client.get_device(device_id))
    ac.set_fahrenheit(int(temp))

def set_vstep(client, device_id, value):
    """Set the configured temperature for an AC device."""

    ac = wideq.ACDevice(client, client.get_device(device_id))
    ac.set_wdirvstep(value)
    
def turn(client, device_id, on_off):
    """Turn on/off an AC device."""

    ac = wideq.ACDevice(client, client.get_device(device_id))
    ac.set_on(on_off == 'on')

def set_reftemp(client, device_id, temp):
    """Set the configured temperature for an AC device."""

    ref = wideq.RefDevice(client, client.get_device(device_id))
    ref.set_reftemp(temp)




def ac_config(client, device_id):
    ac = wideq.ACDevice(client, client.get_device(device_id))
    
    print(ac.get_filter_state())
    print(ac.get_mfilter_state())
    print(ac.get_energy_target())
    print(ac.get_airclean_state())
    print(ac.get_on_time())
    print(ac.get_volume())
    print(ac.get_light())
    print(ac.get_zones())

def wp_config(client, device_id):
    wp = wideq.WPDevice(client, client.get_device(device_id))
    print('day')
    print(wp.day_water_usage('C'))
    print('week')
    print(wp.week_water_usage('C'))
    print('month')
    print(wp.month_water_usage('N'))
    print('year')
    print(wp.year_water_usage('C'))
    print(wp.year_water_usage('N'))    
    print(wp.year_water_usage('H'))

def ac_power(client, device_id):
    ac = wideq.ACDevice(client, client.get_device(device_id))
    print(ac.get_outtotalinstantpower())
    print(ac.get_inoutinstantpower())
    print(ac.get_energy_usage_day())
    print(ac.get_energy_usage_week())
    print(ac.get_energy_usage_month())

def ac_outdoor_temp(client, device_id):
    ac = wideq.ACDevice(client, client.get_device(device_id))
    print(ac.get_outdoor_temp())
    
def ac_dust(client, device_id):
    ac = wideq.Device(client, client.get_device(device_id))
    return ac._get_dustsensor_data()

EXAMPLE_COMMANDS = {
    'ls': ls,
    'mon': mon,
    'dev': getDeviceInfo,
    'model': getModelInfo,
    'ac-mon': ac_mon,
    'set-temp': set_temp,
    'set-reftemp': set_reftemp,
    'turn': turn,
    'ac-config': ac_config,
    'wp-config': wp_config,
    'ac-power': ac_power,
    'set-vstep': set_vstep,
    'ac-outdoor-temp': ac_outdoor_temp,
    'ac-dust': ac_dust
}


def example_command(client, args):
    if not args:
        ls(client)
    else:
        func = EXAMPLE_COMMANDS[args[0]]
        func(client, *args[1:])


def example(args):
    # Load the current state for the example.
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except IOError:
        state = {}

    client = wideq.Client.load(state)

    # Log in, if we don't already have an authentication.
    if not client._auth:
        client._auth = authenticate(client.gateway)

    # Loop to retry if session has expired.
    while True:
        try:
            example_command(client, args)
            break

        except wideq.NotLoggedInError:
            print('Session expired.')
            client.refresh()

    # Save the updated state.
    state = client.dump()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, ensure_ascii = False)


if __name__ == '__main__':
    example(sys.argv[1:])
