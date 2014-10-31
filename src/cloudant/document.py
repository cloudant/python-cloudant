#!/usr/bin/env
"""
_document_

API class for interacting with a document in a database

"""
import json
import posixpath
import urllib


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

