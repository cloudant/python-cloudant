#!/usr/bin/env python
"""
_authentication_

Authentication helper methods


"""

import requests


DEFAULT_URL='https://{username}.cloudant.com/_session'


def get_sso(username, pass_or_token, sso_url=DEFAULT_URL):
    """
    _get_sso_

    """
    url = sso_url.format(username=username)
    resp = requests.get(url, auth=(username, pass_or_token))
    for x in resp.cookies:
        print x


def signin(username, pass_or_token, sso_url=DEFAULT_URL):
    """
    _signin_

    """
    url = sso_url.format(username=username)
    resp = requests.post(url, data={'name': username, 'password': pass_or_token})
    session = resp.cookies.get('AuthSession')
    return session

if __name__ == '__main__':

    signin('evansde77', 'D0gm@t1x')

    get_sso('evansde77', 'D0gm@t1x')
