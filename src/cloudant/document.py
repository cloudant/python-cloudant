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
API module/class for interacting with a document in a database.
"""
import json
import posixpath
import requests
from requests.exceptions import HTTPError

from ._2to3 import url_quote, url_quote_plus
from .error import CloudantException

class Document(dict):
    """
    Encapsulates a JSON document.  A Document object is instantiated with a
    reference to a database and used to manipulate document content
    in a CouchDB or Cloudant database instance.

    In addition to basic CRUD style operations, a Document object also provides
    a convenient context manager.  This context manager removes having to
    explicitly :func:`~cloudant.document.Document.fetch` the document from the
    remote database before commencing work on it as well as explicitly having
    to :func:`~cloudant.document.Document.save` the document once work is
    complete.

    For example:

    .. code-block:: python

        # Upon entry into the document context, fetches the document from the
        # remote database, if it exists. Upon exit from the context, saves the
        # document to the remote database with changes made within the context.
        with Document(database, 'julia006') as document:
            # The document is fetched from the remote database
            # Changes are made locally
            document['name'] = 'Julia'
            document['age'] = 6
            # The document is saved to the remote database

    :param database: A database instance used by the Document.  Can be
        either a ``CouchDatabase`` or ``CloudantDatabase`` instance.
    :param str document_id: Optional document id used to identify the document.
    """
    def __init__(self, database, document_id=None):
        super(Document, self).__init__()
        self._client = database.client
        self._database = database
        self._database_host = self._client.server_url
        self._database_name = database.database_name
        self._document_id = document_id
        if self._document_id is not None:
            self['_id'] = self._document_id
        self.encoder = self._client.encoder

    @property
    def r_session(self):
        """
        Returns the database instance ``r_session`` used by the document.

        :returns: Client ``r_session``
        """
        return self._client.r_session

    @property
    def document_url(self):
        """
        Constructs and returns the document URL.

        :returns: Document URL
        """
        if self._document_id is None:
            return None

        # handle design document url
        if self._document_id.startswith('_design/'):
            return posixpath.join(
                self._database_host,
                url_quote_plus(self._database_name),
                '_design',
                url_quote(self._document_id[8:], safe='')
            )

        # handle document url
        return posixpath.join(
            self._database_host,
            url_quote_plus(self._database_name),
            url_quote(self._document_id, safe='')
        )

    def exists(self):
        """
        Retrieves whether the document exists in the remote database or not.

        :returns: True if the document exists in the remote database,
            otherwise False
        """
        if self._document_id is None:
            return False
        else:
            resp = self.r_session.head(self.document_url)
            if resp.status_code not in [200, 404]:
                resp.raise_for_status()

        return resp.status_code == 200

    def json(self):
        """
        Retrieves the JSON string representation of the current locally cached
        document object, encoded by the encoder specified in the associated
        client object.

        :returns: Encoded JSON string containing the document data
        """
        return json.dumps(dict(self), cls=self.encoder)

    def create(self):
        """
        Creates the current document in the remote database and if successful,
        updates the locally cached Document object with the ``_id``
        and ``_rev`` returned as part of the successful response.
        """
        if self._document_id is not None:
            self['_id'] = self._document_id

        # Ensure that an existing document will not be "updated"
        doc = dict(self)
        if doc.get('_rev') is not None:
            doc.__delitem__('_rev')

        headers = {'Content-Type': 'application/json'}
        resp = self.r_session.post(
            self._database.database_url,
            headers=headers,
            data=json.dumps(doc, cls=self.encoder)
        )
        resp.raise_for_status()
        data = resp.json()
        self._document_id = data['id']
        super(Document, self).__setitem__('_id', data['id'])
        super(Document, self).__setitem__('_rev', data['rev'])
        return

    def fetch(self):
        """
        Retrieves the content of the current document from the remote database
        and populates the locally cached Document object with that content.
        A call to fetch will overwrite any dictionary content currently in
        the locally cached Document object.
        """
        if self.document_url is None:
            raise CloudantException(
                'A document id is required to fetch document contents.  '
                'Add an _id key and value to the document and re-try.'
            )
        resp = self.r_session.get(self.document_url)
        resp.raise_for_status()
        self.clear()
        self.update(resp.json())

    def save(self):
        """
        Saves changes made to the locally cached Document object's data
        structures to the remote database.  If the document does not exist
        remotely then it is created in the remote database.  If the object
        does exist remotely then the document is updated remotely.  In either
        case the locally cached Document object is also updated accordingly
        based on the successful response of the operation.
        """
        headers = {}
        headers.setdefault('Content-Type', 'application/json')
        if not self.exists():
            self.create()
            return
        put_resp = self.r_session.put(
            self.document_url,
            data=self.json(),
            headers=headers
        )
        put_resp.raise_for_status()
        data = put_resp.json()
        super(Document, self).__setitem__('_rev', data['rev'])
        return

    # Update Actions
    # These are handy functions to use with update_field below.
    @staticmethod
    def list_field_append(doc, field, value):
        """
        Appends a value to a list field in a locally cached Document object.
        If a field does not exist it will be created first.

        :param Document doc: Locally cached Document object that can be a
            Document, DesignDocument or dict.
        :param str field: Name of the field list to append to.
        :param value: Value to append to the field list.
        """
        if doc.get(field) is None:
            doc[field] = []
        if not isinstance(doc[field], list):
            raise CloudantException(
                'The field {0} is not a list.'.format(field)
            )
        if value is not None:
            doc[field].append(value)

    @staticmethod
    def list_field_remove(doc, field, value):
        """
        Removes a value from a list field in a locally cached Document object.

        :param Document doc: Locally cached Document object that can be a
            Document, DesignDocument or dict.
        :param str field: Name of the field list to remove from.
        :param value: Value to remove from the field list.
        """
        if not isinstance(doc[field], list):
            raise CloudantException(
                'The field {0} is not a list.'.format(field)
            )
        doc[field].remove(value)

    @staticmethod
    def field_set(doc, field, value):
        """
        Sets or replaces a value for a field in a locally cached Document
        object.  To remove the field set the ``value`` to None.

        :param Document doc: Locally cached Document object that can be a
            Document, DesignDocument or dict.
        :param str field: Name of the field to set.
        :param value: Value to set the field to.
        """
        if value is None:
            doc.__delitem__(field)
        else:
            doc[field] = value

    def _update_field(self, action, field, value, max_tries, tries=0):
        """
        Private update_field method. Wrapped by Document.update_field.
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
        Updates a field in the remote document. If a conflict exists,
        the document is re-fetched from the remote database and the update
        is retried.  This is performed up to ``max_tries`` number of times.

        Use this method when you want to update a single field in a document,
        and don't want to risk clobbering other people's changes to
        the document in other fields, but also don't want the caller
        to implement logic to deal with conflicts.

        For example:

        .. code-block:: python

            # Append the string 'foo' to the 'words' list of Document doc.
            doc.update_field(
                action=doc.list_field_append,
                field='words',
                value='foo'
            )

        :param callable action: A routine that takes a Document object,
            a field name, and a value. The routine should attempt to
            update a field in the locally cached Document object with the
            given value, using whatever logic is appropriate.
            Valid actions are
            :func:`~cloudant.document.Document.list_field_append`,
            :func:`~cloudant.document.Document.list_field_remove`,
            :func:`~cloudant.document.Document.field_set`
        :param str field: Name of the field to update
        :param value: Value to update the field with
        :param int max_tries: In the case of a conflict, the number of retries
            to attempt
        """
        self._update_field(action, field, value, max_tries)

    def delete(self):
        """
        Removes the document from the remote database and clears the content of
        the locally cached Document object with the exception of the ``_id``
        field.  In order to successfully remove a document from the remote
        database, a ``_rev`` value must exist in the locally cached Document
        object.
        """
        if not self.get("_rev"):
            raise CloudantException(
                "Attempting to delete a doc with no _rev. Try running "
                ".fetch first!"
            )

        del_resp = self.r_session.delete(
            self.document_url,
            params={"rev": self["_rev"]},
        )
        del_resp.raise_for_status()
        self.clear()
        self.__setitem__('_id', self._document_id)
        return

    def __enter__(self):
        """
        Supports context like editing of document fields.  Handles context
        entry logic.  Executes a Document.fetch() upon entry.
        """

        # We don't want to raise an exception if the document is not found
        # because upon __exit__ the save() call will create the document
        # if necessary.
        try:
            self.fetch()
        except HTTPError as error:
            if error.response.status_code != 404:
                raise

        return self

    def __exit__(self, *args):
        """
        Support context like editing of document fields.  Handles context exit
        logic.  Executes a Document.save() upon exit.
        """
        self.save()

    def __setitem__(self, key, value):
        """
        Sets the _document_id when setting the '_id' field.
        The _document_id is used to construct the document url.
        """
        if key == '_id':
            self._document_id = value
        super(Document, self).__setitem__(key, value)

    def __delitem__(self, key):
        """
        Sets the _document_id to None when deleting the '_id' field.
        """
        if key == '_id':
            self._document_id = None
        super(Document, self).__delitem__(key)

    def get_attachment(
            self,
            attachment,
            headers=None,
            write_to=None,
            attachment_type=None):
        """
        Retrieves a document's attachment and optionally writes it to a file.
        If the content_type of the attachment is 'application/json' then the
        data returned will be in JSON format otherwise the response content will
        be returned as text or binary.

        :param str attachment: Attachment file name used to identify the
            attachment.
        :param dict headers: Optional, additional headers to be sent
            with request.
        :param file write_to: Optional file handler to write the attachment to.
            The write_to file must be opened for writing prior to including it
            as an argument for this method.
        :param str attachment_type: Optional setting to define how to handle the
            attachment when returning its contents from this method.  Valid
            values are ``'text'``, ``'json'``, and ``'binary'``  If
            omitted then the returned content will be based on the
            response Content-Type.

        :returns: The attachment content
        """
        # need latest rev
        self.fetch()
        attachment_url = posixpath.join(self.document_url, attachment)
        if headers is None:
            headers = {'If-Match': self['_rev']}
        else:
            headers['If-Match'] = self['_rev']

        resp = self.r_session.get(attachment_url, headers=headers)
        resp.raise_for_status()

        if attachment_type is None:
            if resp.headers['Content-Type'].startswith('text/'):
                attachment_type = 'text'
            elif resp.headers['Content-Type'] == 'application/json':
                attachment_type = 'json'
            else:
                attachment_type = 'binary'

        if write_to is not None:
            if attachment_type == 'text' or attachment_type == 'json':
                write_to.write(resp.text)
            else:
                write_to.write(resp.content)
        if attachment_type == 'text':
            return resp.text
        elif attachment_type == 'json':
            return resp.json()

        return resp.content

    def delete_attachment(self, attachment, headers=None):
        """
        Removes an attachment from a remote document and refreshes the locally
        cached document object.

        :param str attachment: Attachment file name used to identify the
            attachment.
        :param dict headers: Optional, additional headers to be sent
            with request.

        :returns: Attachment deletion status in JSON format
        """
        # need latest rev
        self.fetch()
        attachment_url = posixpath.join(self.document_url, attachment)
        if headers is None:
            headers = {'If-Match': self['_rev']}
        else:
            headers['If-Match'] = self['_rev']

        resp = self.r_session.delete(
            attachment_url,
            headers=headers
        )
        resp.raise_for_status()
        super(Document, self).__setitem__('_rev', resp.json()['rev'])
        # Execute logic only if attachment metadata exists locally
        if self.get('_attachments'):
            # Remove the attachment metadata for the specified attachment
            if self['_attachments'].get(attachment):
                self['_attachments'].__delitem__(attachment)
            # Remove empty attachment metadata from the local dictionary
            if not self['_attachments']:
                super(Document, self).__delitem__('_attachments')

        return resp.json()

    def put_attachment(self, attachment, content_type, data, headers=None):
        """
        Adds a new attachment, or updates an existing attachment, to
        the remote document and refreshes the locally cached
        Document object accordingly.

        :param attachment: Attachment file name used to identify the
            attachment.
        :param content_type: The http ``Content-Type`` of the attachment used
            as an additional header.
        :param data: Attachment data defining the attachment content.
        :param headers: Optional, additional headers to be sent
            with request.

        :returns: Attachment addition/update status in JSON format
        """
        # need latest rev
        self.fetch()
        attachment_url = posixpath.join(self.document_url, attachment)
        if headers is None:
            headers = {
                'If-Match': self['_rev'],
                'Content-Type': content_type
            }
        else:
            headers['If-Match'] = self['_rev']
            headers['Content-Type'] = content_type

        resp = self.r_session.put(
            attachment_url,
            data=data,
            headers=headers
        )
        resp.raise_for_status()
        self.fetch()
        return resp.json()
