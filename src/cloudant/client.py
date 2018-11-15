#!/usr/bin/env python
# Copyright (C) 2015, 2018 IBM Corp. All rights reserved.
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
Top level API module that maps to a Cloudant or CouchDB client connection
instance.
"""
import json
from ._2to3 import url_parse

from ._client_session import (
    BasicSession,
    ClientSession,
    CookieSession,
    IAMSession
)
from .database import CloudantDatabase, CouchDatabase
from .feed import Feed, InfiniteFeed
from .error import (
    CloudantArgumentError,
    CloudantClientException,
    CloudantDatabaseException, CloudantException)
from ._common_util import (
    USER_AGENT,
    append_response_error_content,
    CloudFoundryService,
    response_to_json_dict,
    )


class CouchDB(dict):
    """
    Encapsulates a CouchDB client, handling top level user API calls having to
    do with session and database management.

    Maintains a requests.Session for working with the instance specified in the
    constructor.

    Parameters can be passed in to control behavior:

    :param str user: Username used to connect to CouchDB.
    :param str auth_token: Authentication token used to connect to CouchDB.
    :param bool admin_party: Setting to allow the use of Admin Party mode in
        CouchDB.  Defaults to ``False``.
    :param str url: URL for CouchDB server.
    :param str encoder: Optional json Encoder object used to encode
        documents for storage.  Defaults to json.JSONEncoder.
    :param requests.HTTPAdapter adapter: Optional adapter to use for
        configuring requests.
    :param bool connect: Keyword argument, if set to True performs the call to
        connect as part of client construction.  Default is False.
    :param bool auto_renew: Keyword argument, if set to True performs
        automatic renewal of expired session authentication settings.
        Default is False.
    :param float timeout: Timeout in seconds (use float for milliseconds, for
        example 0.1 for 100 ms) for connecting to and reading bytes from the
        server.  If a single value is provided it will be applied to both the
        connect and read timeouts.  To specify different values for each timeout
        use a tuple.  For example, a 10 second connect timeout and a 1 minute
        read timeout would be (10, 60).  This follows the same behaviour as the
        `Requests library timeout argument
        <http://docs.python-requests.org/en/master/user/quickstart/#timeouts>`_.
        but will apply to every request made using this client.
    :param bool use_basic_auth: Keyword argument, if set to True performs basic
        access authentication with server. Default is False.
    :param bool use_iam: Keyword argument, if set to True performs
        IAM authentication with server. Default is False.
        Use :func:`~cloudant.client.CouchDB.iam` to construct an IAM
        authenticated client.
    """
    _DATABASE_CLASS = CouchDatabase

    def __init__(self, user, auth_token, admin_party=False, **kwargs):
        super(CouchDB, self).__init__()
        self._user = user
        self._auth_token = auth_token
        self.server_url = kwargs.get('url')
        self._client_user_header = None
        self.admin_party = admin_party
        self.encoder = kwargs.get('encoder') or json.JSONEncoder
        self.adapter = kwargs.get('adapter')
        self._timeout = kwargs.get('timeout', None)
        self.r_session = None
        self._auto_renew = kwargs.get('auto_renew', False)
        self._use_basic_auth = kwargs.get('use_basic_auth', False)
        self._use_iam = kwargs.get('use_iam', False)
        # If user/pass exist in URL, remove and set variables
        if not self._use_basic_auth and self.server_url:
            parsed_url = url_parse(kwargs.get('url'))
            # Note: To prevent conflicts with field names, the method
            # and attribute names of `url_parse` start with an underscore
            if parsed_url.port is None:
                self.server_url = parsed_url._replace(
                    netloc="{}".format(parsed_url.hostname)).geturl()
            else:
                self.server_url = parsed_url._replace(
                    netloc="{}:{}".format(parsed_url.hostname, parsed_url.port)).geturl()
            if (not user and not auth_token) and (parsed_url.username and parsed_url.password):
                self._user = parsed_url.username
                self._auth_token = parsed_url.password
        self._features = None

        connect_to_couch = kwargs.get('connect', False)
        if connect_to_couch and self._DATABASE_CLASS == CouchDatabase:
            self.connect()

    @property
    def is_iam_authenticated(self):
        """
        Show if a client has authenticated using an IAM API key.

        :return: True if client is IAM authenticated. False otherwise.
        """
        return self._use_iam

    def features(self):
        """
        lazy fetch and cache features
        """
        if self._features is None:
            metadata = self.metadata()
            if "features" in metadata:
                self._features = metadata["features"]
            else:
                self._features = []
        return self._features

    def connect(self):
        """
        Starts up an authentication session for the client using cookie
        authentication if necessary.
        """
        if self.r_session:
            self.session_logout()

        if self.admin_party:
            self._use_iam = False
            self.r_session = ClientSession(
                timeout=self._timeout
            )
        elif self._use_basic_auth:
            self._use_iam = False
            self.r_session = BasicSession(
                self._user,
                self._auth_token,
                self.server_url,
                timeout=self._timeout
            )
        elif self._use_iam:
            self.r_session = IAMSession(
                self._auth_token,
                self.server_url,
                auto_renew=self._auto_renew,
                timeout=self._timeout
            )
        else:
            self.r_session = CookieSession(
                self._user,
                self._auth_token,
                self.server_url,
                auto_renew=self._auto_renew,
                timeout=self._timeout
            )

        # If a Transport Adapter was supplied add it to the session
        if self.adapter is not None:
            self.r_session.mount(self.server_url, self.adapter)
        if self._client_user_header is not None:
            self.r_session.headers.update(self._client_user_header)

        self.session_login()

        # Utilize an event hook to append to the response message
        # using :func:`~cloudant.common_util.append_response_error_content`
        self.r_session.hooks['response'].append(append_response_error_content)

    def disconnect(self):
        """
        Ends a client authentication session, performs a logout and a clean up.
        """
        if self.r_session:
            self.session_logout()

        self.r_session = None
        self.clear()

    def session(self):
        """
        Retrieves information about the current login session
        to verify data related to sign in.

        :returns: Dictionary of session info for the current session.
        """
        return self.r_session.info()

    def session_cookie(self):
        """
        Retrieves the current session cookie.

        :returns: Session cookie for the current session
        """
        return self.r_session.cookies.get('AuthSession')

    def session_login(self, user=None, passwd=None):
        """
        Performs a session login by posting the auth information
        to the _session endpoint.

        :param str user: Username used to connect to server.
        :param str auth_token: Authentication token used to connect to server.
        """
        self.change_credentials(user=user, auth_token=passwd)

    def change_credentials(self, user=None, auth_token=None):
        """
        Change login credentials.

        :param str user: Username used to connect to server.
        :param str auth_token: Authentication token used to connect to server.
        """
        self.r_session.set_credentials(user, auth_token)
        self.r_session.login()

    def session_logout(self):
        """
        Performs a session logout and clears the current session by
        sending a delete request to the _session endpoint.
        """
        self.r_session.logout()

    def basic_auth_str(self):
        """
        Composes a basic http auth string, suitable for use with the
        _replicator database, and other places that need it.

        :returns: Basic http authentication string
        """
        return self.r_session.base64_user_pass()

    def all_dbs(self):
        """
        Retrieves a list of all database names for the current client.

        :returns: List of database names for the client
        """
        url = '/'.join((self.server_url, '_all_dbs'))
        resp = self.r_session.get(url)
        resp.raise_for_status()
        return response_to_json_dict(resp)

    def create_database(self, dbname, **kwargs):
        """
        Creates a new database on the remote server with the name provided
        and adds the new database object to the client's locally cached
        dictionary before returning it to the caller.  The method will
        optionally throw a CloudantClientException if the database
        exists remotely.

        :param str dbname: Name used to create the database.
        :param bool throw_on_exists: Boolean flag dictating whether or
            not to throw a CloudantClientException when attempting to
            create a database that already exists.

        :returns: The newly created database object
        """
        new_db = self._DATABASE_CLASS(self, dbname)
        try:
            new_db.create(kwargs.get('throw_on_exists', False))
        except CloudantDatabaseException as ex:
            if ex.status_code == 412:
                raise CloudantClientException(412, dbname)
        super(CouchDB, self).__setitem__(dbname, new_db)
        return new_db

    def delete_database(self, dbname):
        """
        Removes the named database remotely and locally. The method will throw
        a CloudantClientException if the database does not exist.

        :param str dbname: Name of the database to delete.
        """
        db = self._DATABASE_CLASS(self, dbname)
        if not db.exists():
            raise CloudantClientException(404, dbname)
        db.delete()
        if dbname in list(self.keys()):
            super(CouchDB, self).__delitem__(dbname)

    def db_updates(self, raw_data=False, **kwargs):
        """
        Returns the ``_db_updates`` feed iterator.  While iterating over the
        feed, if necessary, the iteration can be stopped by issuing a call to
        the ``stop()`` method on the returned iterator object.

        For example:

        .. code-block:: python

            # Iterate over a "longpoll" _db_updates feed
            db_updates = client.db_updates()
            for db_update in db_updates:
                if some_condition:
                    db_updates.stop()
                print(db_update)

            # Iterate over a "continuous" _db_updates feed with additional options
            db_updates = client.db_updates(feed='continuous', heartbeat=False)
            for db_update in db_updates:
                if some_condition:
                    db_updates.stop()
                print(db_update)

        :param bool raw_data: If set to True then the raw response data will be
            streamed otherwise if set to False then JSON formatted data will be
            streamed.  Default is False.
        :param str feed: Type of feed.  Valid values are ``continuous``, and
            ``longpoll``.  Default is ``longpoll``.
        :param bool heartbeat: Whether CouchDB will send a newline character
            on timeout. Default is True.
        :param int timeout: Number of seconds to wait for data before
            terminating the response.
        :param int chunk_size: The HTTP response stream chunk size.  Defaults to
            512.

        :returns: Feed object that can be iterated over as a ``_db_updates``
            feed.
        """
        return Feed(self, raw_data, **kwargs)

    def metadata(self):
        """
        Retrieves the remote server metadata dictionary.

        :returns: Dictionary containing server metadata details
        """
        resp = self.r_session.get(self.server_url)
        resp.raise_for_status()
        return response_to_json_dict(resp)

    def keys(self, remote=False):
        """
        Returns the database names for this client. Default is
        to return only the locally cached database names, specify
        ``remote=True`` to make a remote request to include all databases.

        :param bool remote: Dictates whether the list of locally cached
            database names are returned or a remote request is made to include
            an up to date list of databases from the server.  Defaults to False.

        :returns: List of database names
        """
        if not remote:
            return list(super(CouchDB, self).keys())
        return self.all_dbs()

    def __getitem__(self, key):
        """
        Overrides dictionary __getitem__ behavior to provide a database
        instance for the specified key.

        If the database instance does not exist locally, then a remote request
        is made and the database is subsequently added to the local cache and
        returned to the caller.

        If the database instance already exists locally then it is returned and
        a remote request is not performed.

        A KeyError will result if the database does not exist locally or on the
        server.

        :param str key: Database name used to retrieve the database object.

        :returns: Database object
        """
        if key in list(self.keys()):
            return super(CouchDB, self).__getitem__(key)
        db = self._DATABASE_CLASS(self, key)
        if db.exists():
            super(CouchDB, self).__setitem__(key, db)
        else:
            raise KeyError(key)
        return db

    def __delitem__(self, key, remote=False):
        """
        Overrides dictionary __delitem__ behavior to make deleting the
        database key a proxy for deleting the database.  If remote=True then
        it will delete the database on the remote server, otherwise only
        the local cached object will be removed.

        :param str key: Database name of the database to be deleted.
        :param bool remote: Dictates whether the locally cached
            database is deleted or a remote request is made to delete
            the database from the server.  Defaults to False.
        """
        super(CouchDB, self).__delitem__(key)
        if remote:
            self.delete_database(key)

    def get(self, key, default=None, remote=False):
        """
        Overrides dictionary get behavior to retrieve database objects with
        support for returning a default.  If remote=True then a remote
        request is made to retrieve the database from the remote server,
        otherwise the client's locally cached database object is returned.

        :param str key: Database name used to retrieve the database object.
        :param str default: Default database name.  Defaults to None.
        :param bool remote: Dictates whether the locally cached
            database is returned or a remote request is made to retrieve
            the database from the server.  Defaults to False.

        :returns: Database object
        """
        if not remote:
            return super(CouchDB, self).get(key, default)
        db = self._DATABASE_CLASS(self, key)
        if db.exists():
            super(CouchDB, self).__setitem__(key, db)
            return db

        return default

    def __setitem__(self, key, value, remote=False):
        """
        Override dictionary __setitem__ behavior to verify that only
        database instances are added as keys.  If remote=True then also create
        the database remotely if the database does not exist.

        Note:  The only way to override the default for the ``remote`` argument
        setting it to True is to call __setitem__ directly.  A much simpler
        approach is to use
        :func:`~cloudant.client.CouchDB.create_database` instead, if your
        intention is to create a database remotely.

        :param str key: Database name to be used as the key for the database in
            the locally cached dictionary.
        :param value: Database object to be used in the locally cached
            dictionary.
        :param bool remote: Dictates whether the method will attempt to
            create the database remotely or not.  Defaults to False.
        """
        if not isinstance(value, self._DATABASE_CLASS):
            raise CloudantClientException(101, type(value).__name__)
        if remote and not value.exists():
            value.create()
        super(CouchDB, self).__setitem__(key, value)

class Cloudant(CouchDB):
    """
    Encapsulates a Cloudant client, handling top level user API calls having to
    do with session and database management.

    Maintains a requests.Session for working with the
    instance specified in the constructor.

    Parameters can be passed in to control behavior:

    :param str cloudant_user: Username used to connect to Cloudant.
    :param str auth_token: Authentication token used to connect to Cloudant.
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
    :param requests.HTTPAdapter adapter: Optional adapter to use for configuring requests.
    """
    _DATABASE_CLASS = CloudantDatabase

    def __init__(self, cloudant_user, auth_token, **kwargs):
        super(Cloudant, self).__init__(cloudant_user, auth_token, **kwargs)
        self._client_user_header = {'User-Agent': USER_AGENT}
        account = kwargs.get('account')
        if account is not None:
            self.server_url = 'https://{0}.cloudant.com'.format(account)
        if kwargs.get('x_cloudant_user') is not None:
            self._client_user_header['X-Cloudant-User'] = kwargs.get('x_cloudant_user')

        if self.server_url is None:
            raise CloudantClientException(102)

        if kwargs.get('connect', False):
            self.connect()

    def db_updates(self, raw_data=False, **kwargs):
        """
        Returns the ``_db_updates`` feed iterator.  The ``_db_updates`` feed can
        be iterated over and once complete can also provide the last sequence
        identifier of the feed.  If necessary, the iteration can be stopped by
        issuing a call to the ``stop()`` method on the returned iterator object.

        For example:

        .. code-block:: python

            # Iterate over a "normal" _db_updates feed
            db_updates = client.db_updates()
            for db_update in db_updates:
                print(db_update)
            print(db_updates.last_seq)

            # Iterate over a "continuous" _db_updates feed with additional options
            db_updates = client.db_updates(feed='continuous', since='now', descending=True)
            for db_update in db_updates:
                if some_condition:
                    db_updates.stop()
                print(db_update)

        :param bool raw_data: If set to True then the raw response data will be
            streamed otherwise if set to False then JSON formatted data will be
            streamed.  Default is False.
        :param bool descending: Whether results should be returned in
            descending order, i.e. the latest event first. By default, the
            oldest event is returned first.
        :param str feed: Type of feed.  Valid values are ``continuous``,
            ``longpoll``, and ``normal``.  Default is ``normal``.
        :param int heartbeat: Time in milliseconds after which an empty line is
            sent during ``longpoll`` or ``continuous`` if there have been no
            changes.  Must be a positive number.  Default is no heartbeat.
        :param int limit: Maximum number of rows to return.  Must be a positive
            number.  Default is no limit.
        :param since: Start the results from changes after the specified
            sequence identifier. In other words, using since excludes from the
            list all changes up to and including the specified sequence
            identifier. If since is 0 (the default), or omitted, the request
            returns all changes. If it is ``now``, only changes made after the
            time of the request will be emitted.
        :param int timeout: Number of milliseconds to wait for data before
            terminating the response. ``heartbeat`` supersedes ``timeout`` if
            both are supplied.
        :param int chunk_size: The HTTP response stream chunk size.  Defaults to
            512.

        :returns: Feed object that can be iterated over as a ``_db_updates``
            feed.
        """
        return Feed(self, raw_data, **kwargs)

    def infinite_db_updates(self, **kwargs):
        """
        Returns an infinite (perpetually refreshed) ``_db_updates`` feed
        iterator.  If necessary, the iteration can be stopped by issuing a call
        to the ``stop()`` method on the returned iterator object.

        For example:

        .. code-block:: python

            # Iterate over an infinite _db_updates feed
            db_updates = client.infinite_db_updates()
            for db_update in db_updates:
                if some_condition:
                    db_updates.stop()
                print(db_update)

        :param bool descending: Whether results should be returned in
            descending order, i.e. the latest event first. By default, the
            oldest event is returned first.
        :param int heartbeat: Time in milliseconds after which an empty line is
            sent if there have been no changes.  Must be a positive number.
            Default is no heartbeat.
        :param since: Start the results from changes after the specified
            sequence identifier. In other words, using since excludes from the
            list all changes up to and including the specified sequence
            identifier. If since is 0 (the default), or omitted, the request
            returns all changes. If it is ``now``, only changes made after the
            time of the request will be emitted.
        :param int timeout: Number of milliseconds to wait for data before
            terminating the response. ``heartbeat`` supersedes ``timeout`` if
            both are supplied.
        :param int chunk_size: The HTTP response stream chunk size.  Defaults to
            512.

        :returns: Feed object that can be iterated over as a ``_db_updates``
            feed.
        """
        return InfiniteFeed(self, **kwargs)

    def _usage_endpoint(self, endpoint, year=None, month=None):
        """
        Common helper for getting usage and billing reports with
        optional year and month URL elements.

        :param str endpoint: Cloudant usage endpoint.
        :param int year: Year to query against.  Optional parameter.
            Defaults to None.  If used, it must be accompanied by ``month``.
        :param int month: Month to query against that must be an integer
            between 1 and 12. Optional parameter. Defaults to None.
            If used, it must be accompanied by ``year``.
        """
        err = False
        if year is None and month is None:
            resp = self.r_session.get(endpoint)
        else:
            try:
                if int(year) > 0 and int(month) in range(1, 13):
                    resp = self.r_session.get(
                        '/'.join((endpoint, str(int(year)), str(int(month)))))
                else:
                    err = True
            except (ValueError, TypeError):
                err = True

        if err:
            raise CloudantArgumentError(101, year, month)
        else:
            resp.raise_for_status()
            return response_to_json_dict(resp)

    def bill(self, year=None, month=None):
        """
        Retrieves Cloudant billing data, optionally for a given year and month.

        :param int year: Year to query against, for example 2014.
            Optional parameter.  Defaults to None.  If used, it must be
            accompanied by ``month``.
        :param int month: Month to query against that must be an integer
            between 1 and 12.  Optional parameter.  Defaults to None.
            If used, it must be accompanied by ``year``.

        :returns: Billing data in JSON format
        """
        endpoint = '/'.join((self.server_url, '_api', 'v2', 'bill'))
        return self._usage_endpoint(endpoint, year, month)

    def volume_usage(self, year=None, month=None):
        """
        Retrieves Cloudant volume usage data, optionally for a given
        year and month.

        :param int year: Year to query against, for example 2014.
            Optional parameter.  Defaults to None.  If used, it must be
            accompanied by ``month``.
        :param int month: Month to query against that must be an integer
            between 1 and 12.  Optional parameter.  Defaults to None.
            If used, it must be accompanied by ``year``.

        :returns: Volume usage data in JSON format
        """
        endpoint = '/'.join((
            self.server_url, '_api', 'v2', 'usage', 'data_volume'))
        return self._usage_endpoint(endpoint, year, month)

    def requests_usage(self, year=None, month=None):
        """
        Retrieves Cloudant requests usage data, optionally for a given
        year and month.

        :param int year: Year to query against, for example 2014.
            Optional parameter.  Defaults to None.  If used, it must be
            accompanied by ``month``.
        :param int month: Month to query against that must be an integer
            between 1 and 12.  Optional parameter.  Defaults to None.
            If used, it must be accompanied by ``year``.

        :returns: Requests usage data in JSON format
        """
        endpoint = '/'.join((
            self.server_url, '_api', 'v2', 'usage', 'requests'))
        return self._usage_endpoint(endpoint, year, month)

    def shared_databases(self):
        """
        Retrieves a list containing the names of databases shared
        with this account.

        :returns: List of database names
        """
        endpoint = '/'.join((
            self.server_url, '_api', 'v2', 'user', 'shared_databases'))
        resp = self.r_session.get(endpoint)
        resp.raise_for_status()
        data = response_to_json_dict(resp)
        return data.get('shared_databases', [])

    def generate_api_key(self):
        """
        Creates and returns a new API Key/pass pair.

        :returns: API key/pass pair in JSON format
        """
        endpoint = '/'.join((self.server_url, '_api', 'v2', 'api_keys'))
        resp = self.r_session.post(endpoint)
        resp.raise_for_status()
        return response_to_json_dict(resp)

    def cors_configuration(self):
        """
        Retrieves the current CORS configuration.

        :returns: CORS data in JSON format
        """
        endpoint = '/'.join((
            self.server_url, '_api', 'v2', 'user', 'config', 'cors'))
        resp = self.r_session.get(endpoint)
        resp.raise_for_status()

        return response_to_json_dict(resp)

    def disable_cors(self):
        """
        Switches CORS off.

        :returns: CORS status in JSON format
        """
        return self.update_cors_configuration(
            enable_cors=False,
            allow_credentials=False,
            origins=[],
            overwrite_origins=True
        )

    def cors_origins(self):
        """
        Retrieves a list of CORS origins.

        :returns: List of CORS origins
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
        Merges existing CORS configuration with updated values.

        :param bool enable_cors: Enables/disables CORS.  Defaults to True.
        :param bool allow_credentials: Allows authentication credentials.
            Defaults to True.
        :param list origins: List of allowed CORS origin(s).  Special cases are
            a list containing a single "*" which will allow any origin and
            an empty list which will not allow any origin.  Defaults to None.
        :param bool overwrite_origins: Dictates whether the origins list is
            overwritten of appended to.  Defaults to False.

        :returns: CORS configuration update status in JSON format
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
        Overwrites the entire CORS config with the values updated in
        update_cors_configuration.

        :param dict config: Dictionary containing the updated CORS
            configuration.

        :returns: CORS configuration update status in JSON format
        """
        endpoint = '/'.join((
            self.server_url, '_api', 'v2', 'user', 'config', 'cors'))
        resp = self.r_session.put(
            endpoint,
            data=json.dumps(config, cls=self.encoder),
            headers={'Content-Type': 'application/json'}
        )
        resp.raise_for_status()

        return response_to_json_dict(resp)

    @classmethod
    def bluemix(cls, vcap_services, instance_name=None, service_name=None, **kwargs):
        """
        Create a Cloudant session using a VCAP_SERVICES environment variable.

        :param vcap_services: VCAP_SERVICES environment variable
        :type vcap_services: dict or str
        :param str instance_name: Optional Bluemix instance name. Only required
            if multiple Cloudant instances are available.
        :param str service_name: Optional Bluemix service name.

        Example usage:

        .. code-block:: python

            import os
            from cloudant.client import Cloudant

            client = Cloudant.bluemix(os.getenv('VCAP_SERVICES'),
                                      'Cloudant NoSQL DB')

            print client.all_dbs()
        """
        service_name = service_name or 'cloudantNoSQLDB'  # default service
        try:
            service = CloudFoundryService(vcap_services,
                                          instance_name=instance_name,
                                          service_name=service_name)
        except CloudantException:
            raise CloudantClientException(103)

        if hasattr(service, 'iam_api_key'):
            return Cloudant.iam(service.username,
                                service.iam_api_key,
                                url=service.url)
        return Cloudant(service.username,
                        service.password,
                        url=service.url,
                        **kwargs)

    @classmethod
    def iam(cls, account_name, api_key, **kwargs):
        """
        Create a Cloudant client that uses IAM authentication.

        :param account_name: Cloudant account name.
        :param api_key: IAM authentication API key.
        """
        return cls(None,
                   api_key,
                   account=account_name,
                   auto_renew=kwargs.get('auto_renew', True),
                   use_iam=True,
                   **kwargs)
