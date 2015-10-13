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
_account_

Top level API object that maps to a users account.

"""
import base64
import json
import posixpath
import requests
import sys

from .database import CloudantDatabase, CouchDatabase
from .errors import CloudantException

_USER_AGENT = 'python-cloudant/{0} (Python, Version {1}.{2}.{3})'.format(
    sys.modules['cloudant'].__version__,
    sys.version_info[0],
    sys.version_info[1],
    sys.version_info[2])

class CouchDB(dict):
    """
    _CouchDB_

    Object that encapsulates a CouchDB database
    server and user account, handling top level user API calls,
    database creation, token generation et al.

    Maintains a requests.Session for working with the
    account specified in the ctor

    :param url: Host name for couchdb server

    :param encoder: Optional json Encoder object used to encode
        documents for storage. defaults to json.JSONEncoder

    """
    _DATABASE_CLASS = CouchDatabase

    def __init__(self, cloudant_user, auth_token, **kwargs):
        super(CouchDB, self).__init__()
        self._cloudant_user = cloudant_user
        self._cloudant_token = auth_token
        self._cloudant_session = None
        self.cloudant_url = kwargs.get('url')
        self._cloudant_user_header = None
        self.encoder = kwargs.get('encoder') or json.JSONEncoder
        self.r_session = None

    def connect(self):
        """
        _connect_

        Start up an auth session for the account

        """
        self.r_session = requests.Session()
        self.r_session.auth = (self._cloudant_user, self._cloudant_token)
        if self._cloudant_user_header is not None:
            self.r_session.headers.update(self._cloudant_user_header)
        self.session_login(self._cloudant_user, self._cloudant_token)
        self._cloudant_session = self.session()

    def disconnect(self):
        """
        _disconnect_

        End a session, logout and clean up

        """
        self.session_logout()
        del self.r_session

    def session(self):
        """
        _session_

        Retrieve information about the current login session
        to verify data related to sign in.

        :returns: dictionary of session info

        """
        sess_url = posixpath.join(self.cloudant_url, '_session')
        resp = self.r_session.get(sess_url)
        resp.raise_for_status()
        sess_data = resp.json()
        return sess_data

    def session_cookie(self):
        """
        _session_cookie_

        :returns: the current session cookie

        """
        return self.r_session.cookies.get('AuthSession')

    def session_login(self, user, passwd):
        """
        _session_login_

        Perform a session login by posting the auth information
        to the _session endpoint

        """
        sess_url = posixpath.join(self.cloudant_url, '_session')
        resp = self.r_session.post(
            sess_url,
            data={
                'name': user,
                'password': passwd
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        resp.raise_for_status()

    def session_logout(self):
        """
        _session_logout_

        Log out/clear the current session by sending a delete request to
        the cloudant _session endpoint

        """
        sess_url = posixpath.join(self.cloudant_url, '_session')
        resp = self.r_session.delete(
            sess_url
        )
        resp.raise_for_status()

    def basic_auth_str(self):
        """
        Compose a basic http auth string, suitable for use with the
        _replicator database, and other places that need it.

        TODO: I'm not a huge fan of doing basic auth -- need to
        research and see if there's a better way to do this.

        """

        hash_ = base64.urlsafe_b64encode("{username}:{password}".format(
            username=self._cloudant_user,
            password=self._cloudant_token
        ))
        return "Basic {0}".format(hash_)

    def all_dbs(self):
        """
        _all_dbs_

        Return a list of all DB names for this account

        :returns: List of DB name strings

        """
        url = posixpath.join(self.cloudant_url, '_all_dbs')
        resp = self.r_session.get(url)
        resp.raise_for_status()
        return resp.json()

    def create_database(self, dbname, **kwargs):
        """
        _create_database_

        Create a new database in this account with the name provided
        Will optionally throw or not if the db exists

        :param dbname: Name of db to create
        :param throw_on_exists: wether or not to throw CloudantException
           if attempting to create a db that already exists

        :returns: newly created CloudantDatabase instance for the new db

        """
        new_db = self._DATABASE_CLASS(self, dbname)
        if new_db.exists():
            if kwargs.get('throw_on_exists', True):
                raise CloudantException(
                    "Database {0} already exists".format(dbname)
                )
        new_db.create()
        super(CouchDB, self).__setitem__(dbname, new_db)
        return new_db

    def delete_database(self, dbname):
        """
        _delete_database_

        Deletes the named database. Will throw a CloudantException
        if the DB doesnt exist

        :param dbname: Name of the db to delete

        """
        db = self._DATABASE_CLASS(self, dbname)
        if not db.exists():
            raise CloudantException(
                "Database {0} doesnt exist".format(dbname)
            )
        db.delete()
        if dbname in self.keys():
            super(CouchDB, self).__delitem__(dbname)

    def keys(self, remote=False):
        """
        _keys_

        Return the keys/db names for this account. Default is
        to return only the locally cached databases, specify remote=True
        to call out to the DB and include all databases.

        """
        if not remote:
            return super(CouchDB, self).keys()
        return self.all_dbs()

    def __getitem__(self, key):
        """
        _getitem_

        Override getitem behaviour to grab a new database instance for the
        specified key. If the database instance does not exist locally, it is
        added to the cache. If it does it is simply returned.
        If the database does not exist, it will result in a KeyError

        """
        if key in self.keys():
            return super(CouchDB, self).__getitem__(key)
        db = self._DATABASE_CLASS(self, key)
        if db.exists():
            super(CouchDB, self).__setitem__(key, db)
            return db
        else:
            raise KeyError(key)

    def __delitem__(self, key, remote=False):
        """
        _delitem_

        Make deleting the database key a proxy for deleting a database.
        If remote=True it will delete the database, otherwise just the local
        cached object representing it

        """
        super(CouchDB, self).__delitem__(key)
        if remote:
            self.delete_database(key)

    def get(self, key, default=None, remote=False):
        """
        _get_

        Implement the get function to retrieve database objects with support
        for returning a default.
        If remote is True, will call out to check the DB, otherwise uses local
        cached database objects.

        """
        if not remote:
            return super(CouchDB, self).get(key, default)
        db = self._DATABASE_CLASS(self, key)
        if db.exists():
            super(CouchDB, self).__setitem__(key, db)
            return db
        else:
            return default

    def __setitem__(self, key, value, remote=False):
        """
        _setitem_

        Override setitem behaviour to verify that only
        CloudantDatabase instances are added as keys.
        If remote is True, will also create the database
        remotely if it doesnt exist

        """
        if not isinstance(value, self._DATABASE_CLASS):
            msg = "Cannot set key to non CloudantDatabase object"
            raise CloudantException(msg)
        if remote and not value.exists():
            value.create()
        super(CouchDB, self).__setitem__(key, value)


class Cloudant(CouchDB):
    """
    _Cloudant_

    Object that encapsulates a cloudant account,
    handling top level user API calls, database
    creation, token generation et al.

    Maintains a requests.Session for working with the
    account specified in the ctor

    Parameters can be passed in to control behaviour:

    :param cloudant_user: The Cloudant user name.

    :param auth_token: The authentication token for the
      cloudant_user.

    :param account: The Cloudant account name.  If the
      account parameter is present, it will be used to
      construct the Cloudant service URL.

    :param url: If the account is not present and the url
      parameter is present then it will be used to set the
      Cloudant service URL.  The url must be a fully qualified
      https:// URL.

    :param x_cloudant_user: Override the X-Cloudant-User setting
      used to auth. This is needed to auth on someones behalf,
      eg with an admin account.  This parameter must be accompanied
      by the url parameter.  If the url parameter is omitted then
      the x_cloudant_user parameter setting is ignored.

    :param encoder: Optional json Encoder object used to encode
        documents for storage. defaults to json.JSONEncoder

    """
    _DATABASE_CLASS = CloudantDatabase

    def __init__(self, cloudant_user, auth_token, **kwargs):
        super(Cloudant, self).__init__(cloudant_user, auth_token, **kwargs)

        self._cloudant_user_header = {'User-Agent': _USER_AGENT}
        account = kwargs.get('account')
        url = kwargs.get('url')
        x_cloudant_user = kwargs.get('x_cloudant_user')
        if account is not None:
            self.cloudant_url = 'https://{0}.cloudant.com'.format(account)
        elif kwargs.get('url') is not None:
            self.cloudant_url = url
            if x_cloudant_user is not None:
                self._cloudant_user_header['X-Cloudant-User'] = x_cloudant_user

        if self.cloudant_url is None:
            raise CloudantException('You must provide a url or an account.')

    def _usage_endpoint(self, endpoint, year=None, month=None):
        """
        _usage_endpoint_

        Common helper for getting usage and billing reports with
        optional year and month URL elements

        """
        if year is not None:
            endpoint = posixpath.join(endpoint, str(year))
        if month is not None:
            if year is None:
                raise CloudantException(
                    (
                        "must supply both year and month "
                        "to usage endpoint: {0}"
                    ).format(endpoint)
                )
            endpoint = posixpath.join(endpoint, str(month))
        resp = self.r_session.get(endpoint)
        resp.raise_for_status()
        return resp.json()

    def bill(self, year=None, month=None):
        """
        _bill_

        Get your cloudant billing data, optionally for a given year/month

        :param year: int, year, eg 2014
        :param month: int, 1-12

        :returns: JSON billing data structure
        """
        endpoint = posixpath.join(self.cloudant_url, '_api', 'v2', 'bill')
        return self._usage_endpoint(endpoint, year, month)

    def volume_usage(self, year=None, month=None):
        """
        Volume usage for this account.

        :param year: int, year, eg 2014
        :param month: int, 1-12

        """
        endpoint = posixpath.join(
            self.cloudant_url, '_api', 'v2', 'usage', 'data_volume'
        )
        return self._usage_endpoint(endpoint, year, month)

    def requests_usage(self, year=None, month=None):
        """
        Requests usage for this account.

        :param year: int, year, eg 2014
        :param month: int, 1-12

        """
        endpoint = posixpath.join(
            self.cloudant_url, '_api', 'v2', 'usage', 'requests'
        )
        return self._usage_endpoint(endpoint, year, month)

    def shared_databases(self):
        """
        _shared_databases_

        Get a list of databases shared with this account in the format
        cloudant_user/database_name
        """
        endpoint = posixpath.join(
            self.cloudant_url, '_api', 'v2', 'user', 'shared_databases'
        )
        resp = self.r_session.get(endpoint)
        resp.raise_for_status()
        data = resp.json()
        return data.get('shared_databases', [])

    def generate_api_key(self):
        """
        _generate_api_key_

        Create a new API Key/pass pair for accessing this
        account.

        """
        endpoint = posixpath.join(
            self.cloudant_url, '_api', 'v2', 'api_keys'
        )
        resp = self.r_session.post(endpoint)
        resp.raise_for_status()
        return resp.json()

    def cors_configuration(self):
        """

        GET /_api/v2/user/config/cors   Returns the current CORS configuration

        """
        endpoint = posixpath.join(
            self.cloudant_url, '_api', 'v2', 'user', 'config', 'cors'
        )
        resp = self.r_session.get(endpoint)
        resp.raise_for_status()

        return resp.json()

    def disable_cors(self):
        """
        _disable_cors_

        Switch CORS off for this account

        """
        return self.update_cors_configuration(
            enable_cors=False,
            allow_credentials=False,
            origins=[],
            overwrite_origins=True
        )

    def cors_origins(self):
        """
        _cors_origins_

        Retrieve a list of CORS origins

        """
        cors = self.cors_configuration()

        return cors['origins']

    def update_cors_configuration(
            self,
            enable_cors=True,
            allow_credentials=True,
            origins=None,
            overwrite_origins=False):
        """
        _update_cors_configuration_

        Merge existing CORS config with updated values and write to
          the API endpoint

        :param boolean enable_cors: Enable/disables cors
        :param boolean allow_credentials: Allows authentication creds
        :param list origins: Allowed CORS origin(s)
            ["*"]: any origin
            []: disabled/no origin(s)
        :param boolean overwrite_origins: Default concatinate new 'origins'
            list to old one, else replace 'origins' with new list
        """
        if origins is None:
            origins = []

        cors_config = {
            'enable_cors': enable_cors,
            'allow_credentials': allow_credentials,
            'origins': origins
        }

        if overwrite_origins:
            return self._write_cors_configuration(cors_config)

        old_config = self.cors_configuration()

        # update config values
        updated_config = old_config.copy()

        updated_config['enable_cors'] = cors_config.get('enable_cors')
        updated_config['allow_credentials'] = cors_config.get('allow_credentials')

        if cors_config.get('origins') == ["*"]:
            updated_config['origins'] = ["*"]
        elif old_config.get('origins') != cors_config.get('origins'):
            new_origins = list(
                set(old_config.get('origins')).union(
                    set(cors_config.get('origins')))
            )
            updated_config['origins'] = new_origins

        return self._write_cors_configuration(updated_config)

    def _write_cors_configuration(self, config):
        """
        _write_cors_configuration_

        Overwrites the entire CORS config with the values updated in
          update_cors_configuration

        :param dict config: Dictionary containing the updated CORS config

        """
        endpoint = posixpath.join(
            self.cloudant_url, '_api', 'v2', 'user', 'config', 'cors'
        )
        resp = self.r_session.put(
            endpoint,
            data=json.dumps(config),
            headers={'Content-Type': 'application/json'}
        )
        resp.raise_for_status()

        return resp.json()
