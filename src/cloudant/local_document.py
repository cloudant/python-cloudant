#!/usr/bin/env python
# Copyright (c) 2017 IBM. All rights reserved.
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
API module/class for interacting with a local document in a database.
"""
import json
from requests.exceptions import HTTPError

from ._2to3 import url_quote, url_quote_plus
from .error import CloudantLocalDocumentException


class LocalDocument(dict):
    """
    Encapsulates a local document.  Local documents are not replicated to other
    databases, the local document identifier must be known for the local
    document to be accessed, and local documents are not output by views so it
    is impossible to obtain a list of local documents in a database.

    A LocalDocument object is instantiated with a reference to a database and
    used to manipulate local document content in a Cloudant database instance.

    In addition to basic CRUD style operations, a LocalDocument object also
    provides a convenient context manager.  This context manager removes having
    to explicitly :func:`~cloudant.local_document.LocalDocument.fetch` the
    local document from the remote database before commencing work on it as
    well as explicitly having to
    :func:`~cloudant.local_document.LocalDocument.save` the local document once
    work is complete.

    For example:

    .. code-block:: python

        # Upon entry into the local document context, fetches the local
        # document from the remote database, if it exists. Upon exit from the
        # context, saves the local document to the remote database with changes
        # made within the context.
        with LocalDocument(database, '_local/julia006') as local_document:
            # The local document is fetched from the remote database
            # Changes are made locally
            local_document['name'] = 'Julia'
            local_document['age'] = 6
            # The local document is saved to the remote database

    :param database: A ``CloudantDatabase`` instance used by the LocalDocument.
    :param str document_id: Document id used to identify the local document.
    """
    def __init__(self, database, document_id):
        super(LocalDocument, self).__init__()
        self._client = database.client
        self._database = database
        self._database_host = self._client.server_url
        self._database_name = database.database_name
        if not document_id.startswith('_local/'):
            self['_id'] = '_local/{0}'.format(document_id)
        else:
            self['_id'] = document_id
        self.encoder = self._client.encoder

    @property
    def r_session(self):
        """
        Returns the database instance ``requests`` session used by the local
        document.

        :returns: The current ``requests`` session
        """
        return self._client.r_session

    @property
    def document_url(self):
        """
        Constructs and returns the local document URL.

        :returns: Local document URL
        """
        if self.get('_id') is None:
            raise CloudantLocalDocumentException(101)

        return '/'.join(
            [
                self._database_host,
                url_quote_plus(self._database_name),
                '_local',
                url_quote(self['_id'][7:], safe='')
            ]
        )

    def exists(self):
        """
        Retrieves whether the local document exists in the remote database or
        not.

        :returns: True if the local document exists in the remote database,
            otherwise False
        """
        exists = self.r_session.get(self.document_url)
        if exists.status_code not in [200, 404]:
            exists.raise_for_status()

        return exists.status_code == 200

    def json(self):
        """
        Retrieves the JSON string representation of the current locally cached
        local document object, encoded by the encoder specified in the
        associated client object.

        :returns: Encoded JSON string containing the local document data
        """
        return json.dumps(dict(self), cls=self.encoder)

    def create(self):
        """
        Creates or overwrites the current local document in the remote database
        and if successful, updates the locally cached LocalDocument object with
        the ``_rev`` returned as part of the successful response.  Using this
        method guarantees that the local document ``_rev`` will be ``0-1``.
        """
        self.save(reset_revision=True)

    def fetch(self):
        """
        Retrieves the content of the current local document from the remote
        database and populates the locally cached LocalDocument object with
        that content.  A call to fetch will overwrite any dictionary content
        currently in the locally cached LocalDocument object.
        """
        resp = self.r_session.get(self.document_url)
        resp.raise_for_status()
        self.clear()
        self.update(resp.json())

    def save(self, reset_revision=False):
        """
        Saves changes made to the locally cached LocalDocument object's data
        structures to the remote database.  If the local document does not
        exist remotely then it is created in the remote database.  By default
        the revision number of the local document is incremented unless the
        overwrite functionality is requested.

        :param bool reset_revision: Dictates whether the local document
            revision is incremented or reset to ``0-1``.  Default is ``False``
            which is to increment.
        """
        if reset_revision and '_rev' in self.keys():
            self.__delitem__('_rev')
        elif not reset_revision and '_rev' not in self.keys():
            resp = self.r_session.get(self.document_url)
            if resp.status_code == 200:
                data = resp.json()
                self['_rev'] = data['_rev']
            elif resp.status_code != 404:
                resp.raise_for_status()

        put_resp = self.r_session.put(
            self.document_url,
            data=self.json(),
            headers={'Content-Type': 'application/json'}
        )
        put_resp.raise_for_status()
        data = put_resp.json()
        self['_rev'] = data['rev']

    def delete(self):
        """
        Removes the local document from the remote database and clears the
        content of the locally cached LocalDocument object with the exception
        of the ``_id`` field.
        """
        del_resp = self.r_session.delete(self.document_url)
        del_resp.raise_for_status()
        data = del_resp.json()
        self.clear()
        self['_id'] = data['id']

    def __enter__(self):
        """
        Supports context like editing of local document fields.  Handles
        context entry logic.  Executes a LocalDocument.fetch() upon entry.
        """

        # We don't want to raise an exception if the document is not found
        # because upon __exit__ the save() call will create the local document
        # if necessary.
        try:
            self.fetch()
        except HTTPError as err:
            if err.response.status_code != 404:
                raise

        return self

    def __exit__(self, *args):
        """
        Support context like editing of local document fields.  Handles context
        exit logic.  Executes a LocalDocument.save() upon exit.
        """
        self.save()
