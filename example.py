import wideq
import json
import time
import argparse
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

    for device in client.devices:
        print('{0.id}: {0.name} ({0.type.name} {0.model_id})'.format(device))


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
                            except KeyError:
                                print('- {}: {}'.format(key, value))
                            if isinstance(desc, wideq.EnumValue):
                                print('- {}: {}'.format(
                                    key, desc.options.get(value, value)
                                ))
                            elif isinstance(desc, wideq.RangeValue):
                                print('- {0}: {1} ({2.min}-{2.max})'.format(
                                    key, value, desc,
                                ))

        except KeyboardInterrupt:
            pass


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
                    'cur {0.temp_cur_f}°F; '
                    'cfg {0.temp_cfg_f}°F; '
                    'fan speed {0.fan_speed.name}'
                    .format(
                        state,
                        'on' if state.is_on else 'off'
                    )
                )

    except KeyboardInterrupt:
        pass
    finally:
        ac.monitor_stop()


class UserError(Exception):
    """A user-visible command-line error.
    """
    def __init__(self, msg):
        self.msg = msg


def _force_device(client, device_id):
    """Look up a device in the client (using `get_device`), but raise
    UserError if the device is not found.
    """
    device = client.get_device(device_id)
    if not device:
        raise UserError('device "{}" not found'.format(device_id))
    return device


def set_temp(client, device_id, temp):
    """Set the configured temperature for an AC device."""

    ac = wideq.ACDevice(client, _force_device(client, device_id))
    ac.set_fahrenheit(int(temp))


def turn(client, device_id, on_off):
    """Turn on/off an AC device."""

    ac = wideq.ACDevice(client, _force_device(client, device_id))
    ac.set_on(on_off == 'on')


def ac_config(client, device_id):
    ac = wideq.ACDevice(client, _force_device(client, device_id))
    print(ac.get_filter_state())
    print(ac.get_mfilter_state())
    print(ac.get_energy_target())
    print(ac.get_volume())
    print(ac.get_light())
    print(ac.get_zones())


EXAMPLE_COMMANDS = {
    'ls': ls,
    'mon': mon,
    'ac-mon': ac_mon,
    'set-temp': set_temp,
    'turn': turn,
    'ac-config': ac_config,
}


def example_command(client, cmd, args):
    func = EXAMPLE_COMMANDS[cmd]
    func(client, *args)


def example(country, language, cmd, args):
    # Load the current state for the example.
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except IOError:
        state = {}

    client = wideq.Client.load(state)
    if country:
        client._country = country
    if language:
        client._language = language

    # Log in, if we don't already have an authentication.
    if not client._auth:
        client._auth = authenticate(client.gateway)

    # Loop to retry if session has expired.
    while True:
        try:
            example_command(client, cmd, args)
            break

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


def main():
    """The main command-line entry point.
    """
    parser = argparse.ArgumentParser(
        description='Interact with the LG SmartThinQ API.'
    )
    parser.add_argument('cmd', metavar='CMD', nargs='?', default='ls',
                        help='one of {}'.format(', '.join(EXAMPLE_COMMANDS)))
    parser.add_argument('args', metavar='ARGS', nargs='*',
                        help='subcommand arguments')

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
    example(args.country, args.language, args.cmd, args.args)


if __name__ == '__main__':
    main()
