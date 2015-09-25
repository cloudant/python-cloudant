#!/usr/bin/env python
# Copyright (c) 2015 IBM. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
_credentials_

Utilities to support using a ~/.cloudant INI style configuration file
to allow users to pass credentials in

"""
import os
import ConfigParser


def read_dot_couch(
        filename='~/.couch',
        section='couchdb',
        username='user',
        password='password'):
    """
    _read_dot_couch_

    If you have a INI file containing a CouchDB section
    with a username and password in it, you can read it
    to get the credentials with this function.

    :returns: tuple (user, password)

    """
    return _read_dot_file(filename, section, username, password)


def read_dot_cloudant(
        filename='~/.cloudant',
        section='cloudant',
        username='user',
        password='password'):
    """
    _read_dot_cloudant_

    If you have an INI file containing a Cloudant section
    with a username and password in it, you can read it
    to get the credentials with this function.

    :returns: tuple (user, password)

    """
    return _read_dot_file(filename, section, username, password)

def _read_dot_file(filename, section, username, password):
    """
    __read_dot_file_

    Handles the parsing of the configuration file for the username
    and password.
    """
    config_file = os.path.expanduser(filename)
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    username_value = config.get(section, username)
    password_value = config.get(section, password)
    return username_value, password_value
