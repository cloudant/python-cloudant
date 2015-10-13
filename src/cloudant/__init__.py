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
_cloudant_

Cloudant / CouchDB Python Client API

"""
__version__ = '2.0.0a1'

import contextlib

from .account import Cloudant, CouchDB


@contextlib.contextmanager
def cloudant(user, passwd, **kwargs):
    """
    _cloudant_

    Context helper to create a cloudant session and
    provide access to databases, docs etc.

    """
    cloudant_session = Cloudant(user, passwd, **kwargs)
    cloudant_session.connect()
    yield cloudant_session
    cloudant_session.disconnect()


@contextlib.contextmanager
def couchdb(user, passwd, **kwargs):
    """
    _couchdb_

    Context helper to create a couchdb session and
    provide access to databases, docs etc.

    """
    couchdb_session = CouchDB(user, passwd, **kwargs)
    couchdb_session.connect()
    yield couchdb_session
    couchdb_session.disconnect()
