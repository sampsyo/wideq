import wideq


def example():
    gw = wideq.gateway_info()
    oauth_base = gw['empUri']
    api_root = gw['thinqUri']
    print(wideq.oauth_url(oauth_base))

    access_token = wideq.parse_oauth_callback(input())
    print(access_token)

    session_info = wideq.login(api_root, access_token)
    print(session_info)


if __name__ == '__main__':
    example()
