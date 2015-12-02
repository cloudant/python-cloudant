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
Module providing utilities to support using an INI style configuration file
to allow users to pass credentials.
"""
import os
import ConfigParser


def read_dot_couch(
        filename='~/.couch',
        section='couchdb',
        username='user',
        password='password'):
    """
    Provides a way to read an INI file containing a ``couchdb`` section
    that contains authentication credentials for connecting to a
    CouchDB instance.

    :param str filename: Path and name of INI file.  Defaults to ``~/.couch``.
    :param str section: Name of the section in the INI file to find credentials.
        Defaults to ``couchdb``.
    :param str username: Name of the user entry in the INI file and section.
        Defaults to ``user``.
    :param str password: Name of the password entry in the INI file and section.
        Defaults to ``password``.

    :returns: A tuple containing user and password
    """
    return _read_dot_file(filename, section, username, password)


def read_dot_cloudant(
        filename='~/.cloudant',
        section='cloudant',
        username='user',
        password='password'):
    """
    Provides a way to read an INI file containing a ``cloudant`` section
    that contains authentication credentials for connecting to a
    Cloudant instance.

    :param str filename: Path and name of INI file.  Defaults to
        ``~/.cloudant``.
    :param str section: Name of the section in the INI file to find credentials.
        Defaults to ``cloudant``.
    :param str username: Name of the user entry in the INI file and section.
        Defaults to ``user``.
    :param str password: Name of the password entry in the INI file and section.
        Defaults to ``password``.

    :returns: A tuple containing user and password
    """
    return _read_dot_file(filename, section, username, password)

def _read_dot_file(filename, section, username, password):
    """
    Handles the parsing of the configuration file for the username
    and password.

    :param str filename: Path and name of INI file.
    :param str section: Name of the section in the INI file to find credentials.
    :param str username: Name of the user entry in the INI file and section.

    :returns: A tuple containing user and password
    """
    config_file = os.path.expanduser(filename)
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    username_value = config.get(section, username)
    password_value = config.get(section, password)
    return username_value, password_value
