#!/usr/bin/env
"""
_document_

API class for interacting with a document in a database

"""
import json
import posixpath
import urllib
import requests

from .errors import CloudantException


class Document(dict):
    """
    _Document_

    JSON document object, used to manipulate the documents
    in a couch or cloudant database. In addition to basic CRUD
    style operations this provides a context to edit the document:

    with document:
        document['x'] = 'y'

    :param database: CouchDatabase or CloudantDatabase instance
      that the document belongs to
    :param document_id: optional document ID

    """
    def __init__(self, database, document_id=None):
        self._cloudant_account = database._cloudant_account
        self._cloudant_database = database
        self._database_host = self._cloudant_account._cloudant_url
        self._database_name = database._database_name
        self._r_session = database._r_session
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
        """
        :returns: True if the document exists in the database, otherwise False
        """
        resp = self._r_session.get(self._document_url)
        return resp.status_code == 200

    def json(self):
        """
        :returns: JSON string containing the document data, encoded
            with the encoder specified in the owning account
        """
        return json.dumps(dict(self), cls=self._encoder)

    def create(self):
        """
        _create_

        Create this document on the database server,
        update the _id and _rev fields with those of the newly
        created document

        """
        if self._document_id is not None:
            self['_id'] = self._document_id
        headers = {'Content-Type': 'application/json'}

        resp = self._r_session.post(
            self._cloudant_database.database_url,
            headers=headers,
            data=self.json()
        )
        resp.raise_for_status()
        data = resp.json()
        self._document_id = data['id']
        super(Document, self).__setitem__('_id', data['id'])
        super(Document, self).__setitem__('_rev', data['rev'])
        return

    def fetch(self):
        """
        _fetch_

        Fetch the content of this document from the database and update
        self with whatever it finds
        """
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

    # Update Actions
    # These are handy functions to use with update_field below.
    @staticmethod
    def field_append(doc, field, value):
        """Append a value to a field in a doc."""
        doc[field].append(value)

    @staticmethod
    def field_remove(doc, field, value):
        """Remove a value from a field in a doc."""
        doc[field].remove(value)

    @staticmethod
    def field_replace(doc, field, value):
        """Replace a field in a doc with a value."""
        doc[field] = value

    def _update_field(self, action, field, value, max_tries, tries=0):
        """
        Private update_field method. Wrapped by CloudantDocument.update.
        Tracks a "tries" var to help limit recursion.

        """
        # Refresh our view of the document.
        self.fetch()

        # Update the field.
        action(self, field, value)

        # Attempt to save, retrying conflicts up to max_tries.
        try:
            self.save()
        except requests.HTTPError as ex:
            if tries < max_tries and ex.response.status_code == 409:
                return self._update_field(
                    action, field, value, max_tries, tries=tries+1)
            raise

    def update_field(self, action, field, value, max_tries=10):
        """
        _update_field_

        Update a field in the document. If a conflict exists, re-fetch
        the document, and retry the update.

        Use this when you want to update a single field in a document,
        and don't want to risk clobbering other people's changes to
        the document in other fields, but also don't want the caller
        to implement logic to deal with conflicts.

        @param action callable: A routine that takes three arguments:
            A doc, a field, and a value. The routine should attempt to
            update a field in the doc with the given value, using
            whatever logic is appropraite. See this class's
            update_actions property for examples.
        @param field str: the name of the field to update
        @param value: the value to update the field with.
        @param max_tries: in the case of a conflict, give up after this
            number of retries.

        For example, the following will append the string "foo" to the
        "words" list in a Cloudant Document.

        doc.update_field(
            action=doc.field_append,
            field="words",
            value="foo"
        )

        """
        self._update_field(action, field, value, max_tries)

    def delete(self):
        """
        _delete_

        Delete the document on the remote db.

        """
        if not self.get("_rev"):
            raise CloudantException(
                u"Attempting to delete a doc with no _rev. Try running "
                u".fetch first!"
            )

        del_resp = self._r_session.delete(
            self._document_url,
            params={"rev": self["_rev"]},
        )
        del_resp.raise_for_status()
        return

    def __enter__(self):
        """
        support context like editing of document fields
        """
        self.fetch()
        return self

    def __exit__(self, *args):
        self.save()
