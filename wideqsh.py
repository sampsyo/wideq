"""A menu-driven shell for interacting with the LG SmartThinQ API.
"""
import wideq
import json
import time
import argparse
import sys

STATE_FILE = 'wideq_state.json'
client = None

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

def menu(title, items):
    """Display menu
    """

    while True:
        print()
        print(title)
        i = 1
        for item in items:
            if item['active']:
                number = '{: >4d})'.format(i)
            else:
                number = '     '
            print('{0} {1}'.format(number, item['name']))
            i +=1
        print('   e) Exit')
        selection = input('? ');
        if selection.isdigit():
            idx = int(selection) - 1
            if idx >= 0 and idx < len(items) and items[idx]['active']:
                return items[idx]['id']
        elif selection == 'e':
            return None

def select_device():
    """Display device selection menu
    """

    global client

    while True:
        menu_data = []
        for device in client.devices:
            menu_data.append({
                'active': True,
                'id': device,
                'name': '{0.name} ({0.type.name} {0.model_id})'.format(device)
            })
        device = menu('Select device:', menu_data)
        if device is None:
            return
        else:
            show_settings(device)

def show_settings(device):
    """Display device settings menu
    """

    global client

    model = client.model_info(device)
    setmap = json.loads(model.data['ControlWifi']['action']['SetControl']['value'])
    settable = [v[2:-2] for k, v in setmap.items()]
    while True:
        work_id = client.session.monitor_start(device.id)
        while True:
            time.sleep(1)
            raw = client.session.monitor_poll(device.id, work_id)
            if raw is not None:
                break
        client.session.monitor_stop(device.id, work_id)
        mon_data = model.decode_monitor(raw)
        menu_data = []
        for k, v in mon_data.items():
            try:
                value_info = model.value(k)
            except KeyError:
                value_str = v
            if isinstance(value_info, wideq.EnumValue):
                value_str = value_info.options.get(v, v)
            menu_data.append({
                'active': k in settable,
                'id': k,
                'name': '{0}: {1}'.format(k, value_str)
            })
        setting_id = menu('Device: {0.name} ({0.model_id})\nSelect setting to change:'.format(device), menu_data)
        if setting_id is None:
            return
        else:
            change_setting(device, setting_id, mon_data[setting_id])

def change_setting(device, setting_id, value):
    """Change setting
    """

    global client

    title = '\nDevice: {0.name} ({0.model_id})\nSetting: {1}\n'.format(device, setting_id)
    model = client.model_info(device)
    setmap = json.loads(model.data['ControlWifi']['action']['SetControl']['value'])
    reverse_setmap = {v[2:-2]: k for k, v in setmap.items()}
    new_value = None
    try:
        value_info = model.value(setting_id)
        if isinstance(value_info, wideq.RangeValue):
            while True:
                new_value = input(title + 'Enter new value ({0.min}-{0.max} step {0.step}) [{1}]: '.format(value_info, value))
                if new_value == '':
                    new_value = None
                    break
                elif new_value.isdigit():
                    new_value = int(new_value)
                    if new_value >= value_info.min and new_value >= value_info.max and ((new_value - value_info.min) % value_info.step) == 0:
                        break
                print('Invalid input: {0}!'.format(new_value))
        elif isinstance(value_info, wideq.EnumValue):
            menu_data = []
            for k, v in value_info.options.items():
                menu_data.append({
                    'active': True,
                    'id': k,
                    'name': v
                })
            new_value = menu(title + 'Select new value [{0}]:'.format(value_info.options.get(value, value)), menu_data)
            if new_value == value:
                new_value = None
    except KeyError:
        new_value = input(title + 'Enter new value [{0}]: '.format(value))
        if new_value == '':
            new_value = None
    if not new_value is None:
        dev = wideq.Device(client, device)
        dev._set_control(reverse_setmap[setting_id], new_value)

def main():
    """The main entry point.
    """

    global client
    parser = argparse.ArgumentParser(
        description='Interact with the LG SmartThinQ API.'
    )
    parser.add_argument(
        '--country', '-c',
        help='country code for account (default: {})'
        .format(wideq.DEFAULT_COUNTRY)
    )
    parser.add_argument(
        '--language', '-l',
        help='language code for the API (default: {})'
        .format(wideq.DEFAULT_LANGUAGE)
    )
    args = parser.parse_args()

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except IOError:
        state = {}

    client = wideq.Client.load(state)
    if args.country:
        client._country = args.country
    if args.language:
        client._language = args.language

    # Log in, if we don't already have an authentication.
    if not client._auth:
        client._auth = authenticate(client.gateway)

    try:
        select_device()

    except wideq.NotLoggedInError:
        print('Session expired.')
        client.refresh()

    except UserError as exc:
        print(exc.msg, file=sys.stderr)
        sys.exit(1)

    # Save the updated state.
    state = client.dump()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

if __name__ == '__main__':
    main()
