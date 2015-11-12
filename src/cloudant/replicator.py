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
_replicator_

Replication API

"""

import uuid

from .errors import CloudantException
from .document import Document

class Replicator(object):
    """
    Provides a replication API
    """

    def __init__(self, account):
        try:
            self.database = account['_replicator']
        except Exception:
            raise CloudantException(
                'Unable to acquire _replicator database.  '
                'Verify that the account client is valid and try again.'
            )

    def create_replication(self, source_db=None, target_db=None,
                           repl_id=None, **kwargs):
        """
        _create_replication_

        Create a new replication.

        @param Database source_db: Database object to replicate from
        @param Database target_db: Database object to replicate to
        @param str repl_id: replication_id (I'll create one if you
            don't specify.)

        Optional overrides (I'll compose these for you, unless you
            explicitly specify them):
        @param str/dict source: string or dict representing the source
            database, along with authentication info, if any.
        @param str/dict target: string or dict representing the
            target database, possibly including authentication info.
        @param dict user_ctx: User to act as.

        Additional params you might specify (I won't pass these along
            unless specified):
        @param boolean: create_target: specifies whether or not to
            create the target, if it doesn't already exist.
        @param boolean continuous: set to True for a continuous replication.

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
        _list_replications_

        Returns all replication documents.

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
        _replication_state_

        Get the state for the given replication. Possible values are
        "triggered", "completed", "error", and None (this last one is the
        case where the replication is not yet triggered in CouchDB).

        @param str replication_id: id of the replication to inspect.

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
        _follow_replication_

        Block and stream status of a given replication.

        @param str repl_id: id of the replication to follow

        """
        def update_state():
            """
            _update_state_

            Fetch and return the replication state

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
        """ Stop a given replication.

        @param str repl_id: doc id of the replication to stop.

        """

        try:
            repl_doc = self.database[repl_id]
        except KeyError:
            raise CloudantException(
                u"Could not find replication with id {}".format(repl_id))

        repl_doc.fetch()
        repl_doc.delete()
