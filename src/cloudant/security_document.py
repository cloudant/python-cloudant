#!/usr/bin/env python
# Copyright (C) 2016, 2018 IBM. All rights reserved.
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
API module/class for interacting with a security document in a database.
"""
import json

from ._2to3 import url_quote_plus
from ._common_util import response_to_json_dict

class SecurityDocument(dict):
    """
    Encapsulates a JSON security document.  A SecurityDocument object is
    instantiated with a reference to a database and used to manipulate security
    document content in a CouchDB or Cloudant database instance.

    In addition to basic read/write operations, a SecurityDocument object also
    provides a convenient context manager.  This context manager removes having
    to explicitly :func:`~cloudant.security_document.SecurityDocument.fetch`
    the security document from the remote database before commencing work on it
    as well as explicitly having to
    :func:`~cloudant.security_document.SecurityDocument.save` the security
    document once work is complete.

    For example:

    .. code-block:: python

        # Upon entry into the security document context, fetches the security
        # document from the remote database, if it exists. Upon exit from the
        # context, saves the security document to the remote database with
        # changes made within the context.
        with SecurityDocument(database) as security_document:
            # The security document is fetched from the remote database
            # Changes are made locally
            security_document['Cloudant']['julia'] = ['_reader', '_writer']
            security_document['Cloudant']['ruby'] = ['_admin', '_replicator']
            # The security document is saved to the remote database

    :param database: A database instance used by the SecurityDocument.  Can be
        either a ``CouchDatabase`` or ``CloudantDatabase`` instance.
    """
    def __init__(self, database):
        super(SecurityDocument, self).__init__()
        self._client = database.client
        self._database = database
        self._database_host = self._client.server_url
        self._database_name = database.database_name
        self.encoder = self._client.encoder

    @property
    def document_url(self):
        """
        Constructs and returns the security document URL.

        :returns: Security document URL
        """
        return '/'.join([
            self._database_host,
            url_quote_plus(self._database_name),
            '_security'
        ])

    @property
    def r_session(self):
        """
        Returns the Python requests session used by the security document.

        :returns: The Python requests session
        """
        return self._client.r_session

    def json(self):
        """
        Retrieves the JSON string representation of the current locally cached
        security document object, encoded by the encoder specified in the
        associated client object.

        :returns: Encoded JSON string containing the security document data
        """
        return json.dumps(dict(self), cls=self.encoder)

    def fetch(self):
        """
        Retrieves the content of the current security document from the remote
        database and populates the locally cached SecurityDocument object with
        that content.  A call to fetch will overwrite any dictionary content
        currently in the locally cached SecurityDocument object.
        """
        resp = self.r_session.get(self.document_url)
        resp.raise_for_status()
        self.clear()
        self.update(response_to_json_dict(resp))

    def save(self):
        """
        Saves changes made to the locally cached SecurityDocument object's data
        structures to the remote database.
        """
        resp = self.r_session.put(
            self.document_url,
            data=self.json(),
            headers={'Content-Type': 'application/json'}
        )
        resp.raise_for_status()

    def __enter__(self):
        """
        Supports context like editing of security document fields.
        Handles context entry logic.  Executes a
        :func:`~cloudant.security_document.SecurityDocument.fetch` upon entry.
        """
        self.fetch()
        return self

    def __exit__(self, *args):
        """
        Support context like editing of security document fields.
        Handles context exit logic.  Executes a
        :func:`~cloudant.security_document.SecurityDocument.save` upon exit.
        """
        self.save()
