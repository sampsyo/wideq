import wideq
import json
import time
import sys

STATE_FILE = 'wideq_state.json'


def authenticate(gateway):
    login_url = gateway.oauth_url()
    print('Log in here:')
    print(login_url)
    print('Then paste the URL where the browser is redirected:')
    callback_url = input()
    return wideq.Auth.from_url(gateway, callback_url)


def example_command(client, args):
    if not args or args[0] == 'ls':
        for device in client.devices:
            print('{0.id}: {0.name} ({0.model_id})'.format(device))

    elif args[0] == 'mon':
        device_id = args[1]
        device = client.get_device(device_id)
        model = client.model_info(device)

        with wideq.Monitor(client.session, device_id) as mon:
            try:
                while True:
                    time.sleep(1)
                    print('Polling...')
                    res = mon.poll()
                    if res:
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

    elif args[0] == 'ac-mon':
        device_id = args[1]
        ac = wideq.ACDevice(client, client.get_device(device_id))

        try:
            ac.monitor_start()
            while True:
                time.sleep(1)
                state = ac.poll()
                if state:
                    print(
                        'cur {0.temp_cur_f}°F; cfg {0.temp_cfg_f}°F'
                        .format(state)
                    )

        except KeyboardInterrupt:
            pass
        finally:
            ac.monitor_stop()

    elif args[0] == 'set-temp':
        temp = args[1]
        device_id = args[2]

        client.session.set_device_controls(device_id, {'TempCfg': temp})


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
        json.dump(state, f)


if __name__ == '__main__':
    example(sys.argv[1:])
