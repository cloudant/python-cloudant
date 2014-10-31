#!/usr/bin/env python
"""
_dot_cloudant

Utils to support using a ~/.cloudant INI style config file
to let users pass creds in

"""
import os
import ConfigParser

def read_dot_cloudant(
    filename='~/.cloudant',
    section='cloudant',
    username='user',
    password='password'
    ):
    """
    _read_dot_cloudant_

    If you have a ~/.cloudant INI file containing a cloudant
    section with a username and password in it, you can
    read it to get the credentials with this function.

    :returns: tuple (user, passwd)

    """
    config_file = os.path.expanduser(filename)
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    username_value = config.get("cloudant", username)
    password_value = config.get("cloudant", password)
    return username_value, password_value