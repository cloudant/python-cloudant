#!/usr/bin/env python
"""
_account_

Top level cloudant API object that maps to a users account.

"""
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
        _connect
        """
        self._r_session = requests.Session()
        self._r_session.auth = (self._cloudant_user, self._cloudant_token)
        self._r_session.headers.update({'X-Cloudant-User': self._cloudant_user})
        self.session_login(self._cloudant_user, self._cloudant_token)
        self._cloudant_session = self.session()

    def disconnect(self):
        """
        _disconnect_

        """
        self.session_logout()
        del self._r_session

    def session(self):
        sess_url = posixpath.join(self._cloudant_url, '_session')
        resp = self._r_session.get(sess_url)
        resp.raise_for_status()
        sess_data = resp.json()
        return sess_data

    def session_cookie(self):
        return self._r_session.cookies.get('AuthSession')

    def session_login(self, user, passwd):
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
        sess_url = posixpath.join(self._cloudant_url, '_session')
        resp = self._r_session.delete(
            sess_url
        )
        resp.raise_for_status()

    def set_permissions(self):
        #TODO implement this when available in v2
        pass

    def generate_api_key(self):
        # TODO implement this when available in v2
        pass

    def all_dbs(self):
        url = posixpath.join(self._cloudant_url, '_all_dbs')
        resp = self._r_session.get(url)
        resp.raise_for_status()
        return resp.json()

    def create_database(self, dbname, **kwargs):
        """
        _create_database_

        Create a new database in this account

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

        """
        db = CloudantDatabase(self, dbname)
        if not db.exists():
            raise CloudantException("Database {0} doesnt exist".format(dbname))
        db.delete()
        if dbname in self.keys():
            super(Cloudant, self).__delitem__(dbname)


    def keys(self, remote=False):
        if not remote:
            return super(Cloudant, self).keys()
        return self.all_dbs()

    def __getitem__(self, key):
        if key in self.keys():
            return super(Cloudant, self).__getitem__(key)
        db = CloudantDatabase(self, key)
        if db.exists():
            super(Cloudant, self).__setitem__(key, db)
            return db
        else:
            raise KeyError(key)

    def __delitem__(self, key):
        self.delete_database(key)

    def get(self, key, default=None, remote=False):
        if not remote:
            return super(Cloudant, self).get(key, default)
        db = CloudantDatabase(self, key)
        if db.exists():
            super(Cloudant, self).__setitem__(key, db)
            return db
        else:
            return default

    def __setitem__(self, key, value):
        if not isinstance(value, CloudantDatabase):
            msg = "Cannot set key to non CloudantDatabase object"
            raise CloudantException(msg)
        if not value.exists():
            value.create()
        super(Cloudant, self).__setitem__(key, value)


