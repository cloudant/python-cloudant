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
Cloudant / CouchDB Python client library API package
"""
__version__ = '2.0.0b1'

# pylint: disable=wrong-import-position
import contextlib
# pylint: disable=wrong-import-position
from .account import Cloudant, CouchDB

@contextlib.contextmanager
def cloudant(user, passwd, **kwargs):
    """
    Provides a context manager to create a Cloudant session and
    provide access to databases, docs etc.

    :param str user: Username used to connect to Cloudant.
    :param str passwd: Authentication token used to connect to Cloudant.
    :param str account: The Cloudant account name.  If the account parameter
        is present, it will be used to construct the Cloudant service URL.
    :param str url: If the account is not present and the url parameter is
        present then it will be used to set the Cloudant service URL.  The
        url must be a fully qualified http/https URL.
    :param str x_cloudant_user: Override the X-Cloudant-User setting used to
        authenticate. This is needed to authenticate on one's behalf,
        eg with an admin account.  This parameter must be accompanied
        by the url parameter.  If the url parameter is omitted then
        the x_cloudant_user parameter setting is ignored.
    :param str encoder: Optional json Encoder object used to encode
        documents for storage. Defaults to json.JSONEncoder.

    For example:

    .. code-block:: python

        # cloudant context manager
        from cloudant import cloudant

        with cloudant(USERNAME, PASSWORD, account=ACCOUNT_NAME) as client:
            # Context handles connect() and disconnect() for you.
            # Perform library operations within this context.  Such as:
            print client.all_dbs()
            # ...
    """
    cloudant_session = Cloudant(user, passwd, **kwargs)
    cloudant_session.connect()
    yield cloudant_session
    cloudant_session.disconnect()

@contextlib.contextmanager
def couchdb(user, passwd, **kwargs):
    """
    Provides a context manager to create a CouchDB session and
    provide access to databases, docs etc.

    :param str user: Username used to connect to CouchDB.
    :param str passwd: Passcode used to connect to CouchDB.
    :param str url: URL for CouchDB server.
    :param str encoder: Optional json Encoder object used to encode
        documents for storage.  Defaults to json.JSONEncoder.

    For example:

    .. code-block:: python

        # couchdb context manager
        from cloudant import couchdb

        with couchdb(USERNAME, PASSWORD, url=COUCHDB_URL) as client:
            # Context handles connect() and disconnect() for you.
            # Perform library operations within this context.  Such as:
            print client.all_dbs()
            # ...
    """
    couchdb_session = CouchDB(user, passwd, **kwargs)
    couchdb_session.connect()
    yield couchdb_session
    couchdb_session.disconnect()
