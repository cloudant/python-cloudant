#!/usr/bin/env python
"""
_account_

Top level cloudant API object that maps to a users account.

"""
import base64
import json
import posixpath
import requests

from .database import CloudantDatabase
from .errors import CloudantException


class Cloudant(dict):
    """
    _Cloudant_

    Object that encapsulates a cloudant account,
    handling top level user API calls, database
    creation, token generation et al.

    Maintains a requests.Session for working with the
    account specified in the ctor

    """
    def __init__(self, cloudant_user, auth_token, **kwargs):
        super(Cloudant, self).__init__()
        self._cloudant_user = cloudant_user
        self._cloudant_token = auth_token
        self._cloudant_session = None
        self._cloudant_url = kwargs.get("cloudant_url") or "https://{0}.cloudant.com".format(self._cloudant_user)
        self._encoder=kwargs.get('encoder') or json.JSONEncoder

    def connect(self):
        """
        _connect_

        Start up an auth session for the account

        """
        self._r_session = requests.Session()
        self._r_session.auth = (self._cloudant_user, self._cloudant_token)
        self._r_session.headers.update({'X-Cloudant-User': self._cloudant_user})
        self.session_login(self._cloudant_user, self._cloudant_token)
        self._cloudant_session = self.session()

    def disconnect(self):
        """
        _disconnect_

        End a session, logout and clean up

        """
        self.session_logout()
        del self._r_session

    def session(self):
        """
        _session_

        Retrieve information about the current login session
        to verify data related to sign in.

        :returns: dictionary of session info

        """
        sess_url = posixpath.join(self._cloudant_url, '_session')
        resp = self._r_session.get(sess_url)
        resp.raise_for_status()
        sess_data = resp.json()
        return sess_data

    def session_cookie(self):
        """
        _session_cookie_

        :returns: the current session cookie

        """
        return self._r_session.cookies.get('AuthSession')

    def session_login(self, user, passwd):
        """
        _session_login_

        Perform a session login by posting the auth information
        to the _session endpoint

        """
        sess_url = posixpath.join(self._cloudant_url, '_session')
        resp = self._r_session.post(
            sess_url,
            data={
                'name': self._cloudant_user,
                'password': self._cloudant_token
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
        sess_url = posixpath.join(self._cloudant_url, '_session')
        resp = self._r_session.delete(
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

    def set_permissions(self):
        #TODO implement this when available in v2
        pass

    def generate_api_key(self):
        # TODO implement this when available in v2
        pass

    def all_dbs(self):
        """
        _all_dbs_

        Return a list of all DB names for this account

        :returns: List of DB name strings

        """
        url = posixpath.join(self._cloudant_url, '_all_dbs')
        resp = self._r_session.get(url)
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
        new_db = CloudantDatabase(self, dbname)
        if new_db.exists():
            if kwargs.get('throw_on_exists', True):
                raise CloudantException("Database {0} already exists".format(dbname))
        new_db.create()
        super(Cloudant, self).__setitem__(dbname, new_db)
        return new_db

    def delete_database(self, dbname):
        """
        _delete_database_

        Deletes the named database. Will throw a CloudantException
        if the DB doesnt exist

        :param dbname: Name of the db to delete

        """
        db = CloudantDatabase(self, dbname)
        if not db.exists():
            raise CloudantException("Database {0} doesnt exist".format(dbname))
        db.delete()
        if dbname in self.keys():
            super(Cloudant, self).__delitem__(dbname)

    def keys(self, remote=False):
        """
        _keys_

        Return the keys/db names for this account. Default is
        to return only the locally cached databases, specify remote=True
        to call out to the DB and include all databases.

        """
        if not remote:
            return super(Cloudant, self).keys()
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
            return super(Cloudant, self).__getitem__(key)
        db = CloudantDatabase(self, key)
        if db.exists():
            super(Cloudant, self).__setitem__(key, db)
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
        super(Cloudant, self).__delitem__(key)
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
            return super(Cloudant, self).get(key, default)
        db = CloudantDatabase(self, key)
        if db.exists():
            super(Cloudant, self).__setitem__(key, db)
            return db
        else:
            return default

    def __setitem__(self, key, value, remote=False):
        """
        _setitem_

        Override setitem behaviour to verify that only CloudantDatabase instances
        are added as keys.
        If remote is True, will also create the database remotely if it doesnt exist

        """
        if not isinstance(value, CloudantDatabase):
            msg = "Cannot set key to non CloudantDatabase object"
            raise CloudantException(msg)
        if remote and not value.exists():
            value.create()
        super(Cloudant, self).__setitem__(key, value)


