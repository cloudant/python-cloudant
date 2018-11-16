#!/usr/bin/env python
# Copyright (c) 2015, 2018 IBM. All rights reserved.
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
__version__ = '2.10.1'

# pylint: disable=wrong-import-position
import contextlib
# pylint: disable=wrong-import-position
from .client import Cloudant, CouchDB
from ._common_util import CloudFoundryService

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
def cloudant_iam(account_name, api_key, **kwargs):
    """
    Provides a context manager to create a Cloudant session using IAM
    authentication and provide access to databases, docs etc.

    :param account_name: Cloudant account name.
    :param api_key: IAM authentication API key.

    For example:

    .. code-block:: python

        # cloudant context manager
        from cloudant import cloudant_iam

        with cloudant_iam(ACCOUNT_NAME, API_KEY) as client:
            # Context handles connect() and disconnect() for you.
            # Perform library operations within this context.  Such as:
            print client.all_dbs()
            # ...

    """
    cloudant_session = Cloudant.iam(account_name, api_key, **kwargs)

    cloudant_session.connect()
    yield cloudant_session
    cloudant_session.disconnect()

@contextlib.contextmanager
def cloudant_bluemix(vcap_services, instance_name=None, service_name=None, **kwargs):
    """
    Provides a context manager to create a Cloudant session and provide access
    to databases, docs etc.

    :param vcap_services: VCAP_SERVICES environment variable
    :type vcap_services: dict or str
    :param str instance_name: Optional Bluemix instance name. Only required if
        multiple Cloudant instances are available.
    :param str service_name: Optional Bluemix service name.
    :param str encoder: Optional json Encoder object used to encode
        documents for storage. Defaults to json.JSONEncoder.

    Loads all configuration from the specified VCAP_SERVICES Cloud Foundry
    environment variable. The VCAP_SERVICES variable contains connection
    information to access a service instance. For example:

    .. code-block:: json

        {
            "VCAP_SERVICES": {
                "cloudantNoSQLDB": [
                    {
                        "credentials": {
                            "apikey": "some123api456key"
                            "username": "example",
                            "password": "xxxxxxx",
                            "host": "example.cloudant.com",
                            "port": 443,
                            "url": "https://example:xxxxxxx@example.cloudant.com"
                        },
                        "syslog_drain_url": null,
                        "label": "cloudantNoSQLDB",
                        "provider": null,
                        "plan": "Lite",
                        "name": "Cloudant NoSQL DB"
                    }
                ]
            }
        }

    See `Cloud Foundry Environment Variables <http://docs.cloudfoundry.org/
    devguide/deploy-apps/environment-variable.html#VCAP-SERVICES>`_.

    Example usage:

    .. code-block:: python

        import os

        # cloudant_bluemix context manager
        from cloudant import cloudant_bluemix

        with cloudant_bluemix(os.getenv('VCAP_SERVICES'), 'Cloudant NoSQL DB') as client:
            # Context handles connect() and disconnect() for you.
            # Perform library operations within this context.  Such as:
            print client.all_dbs()
            # ...
    """
    cloudant_session = Cloudant.bluemix(
        vcap_services,
        instance_name=instance_name,
        service_name=service_name,
        **kwargs
    )
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

@contextlib.contextmanager
def couchdb_admin_party(**kwargs):
    """
    Provides a context manager to create a CouchDB session in Admin Party mode
    and provide access to databases, docs etc.

    :param str url: URL for CouchDB server.
    :param str encoder: Optional json Encoder object used to encode
        documents for storage.  Defaults to json.JSONEncoder.

    For example:

    .. code-block:: python

        # couchdb_admin_party context manager
        from cloudant import couchdb_admin_party

        with couchdb_admin_party(url=COUCHDB_URL) as client:
            # Context handles connect() and disconnect() for you.
            # Perform library operations within this context.  Such as:
            print client.all_dbs()
            # ...
    """
    couchdb_session = CouchDB(None, None, True, **kwargs)
    couchdb_session.connect()
    yield couchdb_session
    couchdb_session.disconnect()
