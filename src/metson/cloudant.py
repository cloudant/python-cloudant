#!/usr/bin/env python
"""
_cloudant_

"""

import contextlib
import json
import posixpath
import requests
import urllib


@contextlib.contextmanager
def cloudant(user, passwd, **kwargs):
    c = Cloudant(user, passwd, **kwargs)
    c.connect()
    yield c
    c.disconnect()



class CloudantException(Exception):
    """
    _CloudantException_

    """
    def __init__(self, msg, code=None):
        super(CloudantException, self).__init__(msg)
        self.status_code = code



class CloudantDocument(dict):
    """
    _CloudantDocument_

    """
    def __init__(self, cloudant_database, document_id=None):
        self._cloudant_account = cloudant_database._cloudant_account
        self._cloudant_database = cloudant_database
        self._database_host = self._cloudant_account._cloudant_url
        self._database_name = cloudant_database._database_name
        self._r_session = cloudant_database._r_session
        self._document_id = document_id
        self._encoder = self._cloudant_account._encoder

    _document_url = property(
            lambda x: posixpath.join(
                x._database_host,
                urllib.quote_plus(x._database_name),
                x._document_id
            )
        )

    def exists(self):
        resp = self._r_session.get(self._document_url)
        return resp.status_code == 200

    def json(self):
        return json.dumps(dict(self), cls=self._encoder)

    def create(self):
        """
        _create_

        Create this document

        """
        if self._document_id is not None:
            self['_id'] = self._document_id
        headers = {'Content-Type': 'application/json'}

        resp = self._r_session.post(
            self._cloudant_database._database_url,
            headers=headers,
            data=self.json()
        )
        resp.raise_for_status()
        data = resp.json()
        self._document_id = data['id']
        super(CloudantDocument, self).__setitem__('_id', data['id'])
        super(CloudantDocument, self).__setitem__('_rev', data['rev'])
        return

    def fetch(self):
        resp = self._r_session.get(self._document_url)
        resp.raise_for_status()
        self.update(resp.json())

    def save(self):
        """
        _save_

        Save changes made to this objects data structures back to the
        database document, essentially an update CRUD call but we
        dont want to conflict with dict.update

        """

        headers = {}
        headers.setdefault('Content-Type', 'application/json')
        if not self.exists():
            self.create()
            return
        put_resp = self._r_session.put(
            self._document_url,
            data=self.json(),
            headers=headers
        )
        put_resp.raise_for_status()
        return

    def __enter__(self):
        """
        support context like editing of document fields
        """
        self.fetch()
        return self

    def __exit__(self, *args):
        self.save()


class CloudantDatabase(dict):
    """
    _CloudantDatabase_

    """
    def __init__(self, cloudant, database_name):
        super(CloudantDatabase, self).__init__()
        self._cloudant_account = cloudant
        self._database_host = cloudant._cloudant_url
        self._database_name = database_name
        self._r_session = cloudant._r_session

    _database_url = property(
            lambda x: posixpath.join(
                x._database_host,
                urllib.quote_plus(x._database_name)
            )
        )


    def exists(self):
        resp = self._r_session.get(self._database_url)
        return resp.status_code == 200

    def metadata(self):
        resp = self._r_session.get(self._database_url)
        resp.raise_for_status()
        return resp.json()

    def doc_count(self):
        return self._metadata().get('doc_count')

    def create_document(self, data, throw_on_exists=False):
        doc = CloudantDocument(self, data.get('_id'))
        doc.update(data)
        doc.create()
        return doc

    def new_document(self):
        """
        _new_document_

        Creates new, empty document
        """
        doc = CloudantDocument(self, None)
        doc.create()
        return doc

    def create(self):
        """
        _create_

        Create this database if it doesnt exist
        """
        if self.exists():
            return self

        resp = self._r_session.put(self._database_url)
        if resp.status_code == 201:
            return self

        raise CloudantException(
            u"Unable to create database {0}: Reason:{1}".format(
                self._database_url, resp.text
            ),
            code=resp.status_code
        )

    def delete(self):
        """
        _delete_

        Delete this database

        """
        resp = self._r_session.delete(self._database_url)
        resp.raise_for_status()

    def all_docs(self, **kwargs):
        """

        descending  Return the documents in descending by key order boolean false
        endkey  Stop returning records when the specified key is reached string
        include_docs    Include the full content of the documents in the return boolean false
        inclusive_end   Include rows whose key equals the endkey  boolean true
        key Return only documents that match the specified key  string
        limit   Limit the number of the returned documents to the specified number  numeric
        skip    Skip this number of records before starting to return the results  numeric 0
        startkey

        """
        resp = self._r_session.get(posixpath.join(self._database_url, '_all_docs'), params=dict(kwargs))
        data = resp.json()
        return data

    def keys(self, remote=False):
        """
        _keys_

        """
        if not remote:
            return super(CloudantDatabase, self).keys()
        docs = self.all_docs()
        return [ row['id'] for row in docs.get('rows', []) ]

    def __getitem__(self, key):
        if key in self.keys():
            return super(CloudantDatabase, self).__getitem__(key)
        doc = CloudantDocument(self, key)
        if doc.exists():
            doc.fetch()
            super(CloudantDatabase, self).__setitem__(key, doc)
            return doc
        else:
            raise KeyError(key)





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




if __name__ == '__main__':
    with cloudant('evansde77', 'D0gm@t1x') as cloudant:

        print cloudant.keys(remote=True)
        print cloudant['towed_vehicles'].exists()
        #cloudant['not_a_db']

        #print cloudant['towed_vehicles']._metadata()
        #print cloudant['towed_vehicles']._all_docs()
        # for x in cloudant.towed_vehicles._iter_all_docs():
        #     print x
        #print cloudant['towed_vehicles'].all_docs()
        print cloudant['towed_vehicles']['00011E63-255D-4BC2-9524-53EC1A6F52E0']['Style']
        #print cloudant['towed_vehicles'].keys()
        print cloudant['towed_vehicles'].keys(remote=True)


        print cloudant.create_database("test_api", throw_on_exists=False)
        print cloudant.keys()
        print cloudant.keys(remote=True)
        doc = cloudant['test_api'].create_document({"test": 123})
        print doc
        doc2 = cloudant['test_api'].create_document({"_id": "womp", "test":345})
        print doc2
        with cloudant['test_api']['womp'] as working_doc:
            working_doc['new_field'] = {"aa":"bb"}
            working_doc['test'] = ['a', 'b', 'c']

        with cloudant['test_api'].new_document() as working_doc:
            working_doc['tweak'] = "weasel"
            print working_doc


        print cloudant.delete_database("test_api")
        print cloudant.keys()
        print cloudant.keys(remote=True)
