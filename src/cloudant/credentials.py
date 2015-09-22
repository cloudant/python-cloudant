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
_dot_cloudant

Utils to support using a ~/.cloudant INI style config file
to let users pass creds in

"""
import os
import ConfigParser


def read_dot_couch(
        filename='~/.couch',
        section='cloudant',
        username='user',
        password='password'):
    config_file = os.path.expanduser(filename)
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    username_value = config.get("couchdb", username)
    password_value = config.get("couchdb", password)
    return username_value, password_value


def read_dot_cloudant(
        filename='~/.cloudant',
        section='cloudant',
        username='user',
        password='password'):
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
