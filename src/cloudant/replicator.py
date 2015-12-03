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
API module/class for handling database replications
"""

import uuid

from .errors import CloudantException
from .document import Document

class Replicator(object):
    """
    Provides a database replication API.  A Replicator object is instantiated
    with a reference to a client/session.  It retrieves the ``_replicator``
    database for the specified client and uses that database object to manage
    replications.

    :param client: Client instance used by the database.  Can either be a
        ``CouchDB`` or ``Cloudant`` client instance.
    """

    def __init__(self, client):
        try:
            self.database = client['_replicator']
        except Exception:
            raise CloudantException(
                'Unable to acquire _replicator database.  '
                'Verify that the account client is valid and try again.'
            )

    def create_replication(self, source_db=None, target_db=None,
                           repl_id=None, **kwargs):
        """
        Creates a new replication task.

        :param source_db: Database object to replicate from.  Can be either a
            ``CouchDatabase`` or ``CloudantDatabase`` instance.
        :param target_db: Database object to replicate to.  Can be either a
            ``CouchDatabase`` or ``CloudantDatabase`` instance.
        :param str repl_id: Optional replication id.  Generated internally if
            not explicitly set.
        :param source: Optional ``str`` or ``dict`` representing the source
            database, along with authentication info, if any.  Composed
            internally if not explicitly set.
        :param target: Optional ``str`` or ``dict`` representing the
            target database, possibly including authentication info.  Composed
            internally if not explicitly set.
        :param dict user_ctx: Optional user to act as.  Composed internally
            if not explicitly set.
        :param bool create_target: Specifies whether or not to
            create the target, if it does not already exist.
        :param bool continuous: If set to True then the replication will be
            continuous.

        :returns: Replication document as a Document instance
        """

        data = dict(
            _id=repl_id if repl_id else unicode(uuid.uuid4()),
            **kwargs
        )

        if not data.get('source'):
            if source_db is None:
                raise CloudantException(
                    u"You must specify either a source_db Database "
                    u"object or a manually composed 'source' string/dict."
                )
            data['source'] = {
                "url": source_db.database_url,
                "headers": {
                    "Authorization": source_db.creds['basic_auth']
                }
            }

        if not data.get('target'):
            if target_db is None:
                raise CloudantException(
                    u"You must specify either a target_db Database "
                    u"object or a manually composed 'target' string/dict."
                )
            data['target'] = {
                "url": target_db.database_url,
                "headers": {
                    "Authorization": target_db.creds['basic_auth']
                }
            }

        if not data.get('user_ctx'):
            data['user_ctx'] = self.database.creds['user_ctx']

        return self.database.create_document(data, throw_on_exists=True)

    def list_replications(self):
        """
        Retrieves all replication documents from the replication database.

        :returns: List containing replication Document objects
        """
        docs = self.database.all_docs(include_docs=True)['rows']
        documents = []
        for doc in docs:
            document = {}
            if doc['id'].startswith('_design/'):
                continue
            document = Document(self.database, doc['id'])
            document.update(doc['doc'])
            documents.append(document)
        return documents

    def replication_state(self, repl_id):
        """
        Retrieves the state for the given replication. Possible values are
        ``triggered``, ``completed``, ``error``, and ``None`` (meaning not yet
        triggered).

        :param str repl_id: Replication id used to identify the replication to
            inspect.

        :returns: Replication state as a ``str``
        """
        try:
            repl_doc = self.database[repl_id]
        except KeyError:
            raise CloudantException(
                "Replication {} not found".format(repl_id)
            )
        repl_doc.fetch()
        return repl_doc.get('_replication_state')

    def follow_replication(self, repl_id):
        """
        Blocks and streams status of a given replication.

        For example:

        .. code-block:: python

            for doc in replicator.follow_replication(repl_doc_id):
                # Process replication information as it comes in

        :param str repl_id: Replication id used to identify the replication to
            inspect.

        :returns: Iterable stream of copies of the replication Document
            and replication state as a ``str`` for the specified replication id
        """
        def update_state():
            """
            Retrieves the replication state.
            """
            try:
                repl_doc = self.database[repl_id]
                repl_doc.fetch()
                state = repl_doc.get('_replication_state')
            except KeyError:
                repl_doc = None
                state = None

            return repl_doc, state

        while True:
            # Make sure we fetch the state up front, just in case it moves
            # too fast and we miss it in the changes feed.
            repl_doc, state = update_state()
            if repl_doc:
                yield repl_doc
            if state is not None and state in ['error', 'completed']:
                raise StopIteration

            # Now listen on changes feed for the state
            for change in self.database.changes():
                if change.get('id') == repl_id:
                    repl_doc, state = update_state()
                    if repl_doc is not None:
                        yield repl_doc
                    if state is not None and state in ['error', 'completed']:
                        raise StopIteration

    def stop_replication(self, repl_id):
        """
        Stops a replication based on the provided replication id by deleting
        the replication document from the replication database.  The
        replication can only be stopped if it has not yet completed.  If it has
        already completed then the replication document is still deleted from
        replication database.

        :param str repl_id: Replication id used to identify the replication to
            stop.
        """

        try:
            repl_doc = self.database[repl_id]
        except KeyError:
            raise CloudantException(
                u"Could not find replication with id {}".format(repl_id))

        repl_doc.fetch()
        repl_doc.delete()
