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
_replicator_tests_

replicator module - Unit tests for the Replicator class

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import uuid
import time
import requests
import os

from cloudant.replicator import Replicator
from cloudant.document import Document
from cloudant.errors import CloudantException

from .unit_t_db_base import UnitTestDbBase
from ... import unicode_

class ReplicatorTests(UnitTestDbBase):
    """
    Replicator unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(ReplicatorTests, self).setUp()
        self.db_set_up()
        self.test_target_dbname = self.dbname()
        self.target_db = self.client._DATABASE_CLASS(
            self.client,
            self.test_target_dbname
        )
        self.target_db.create()
        self.replicator = Replicator(self.client)
        self.replication_ids = []

    def tearDown(self):
        """
        Reset test attributes
        """
        self.target_db.delete()
        del self.test_target_dbname
        del self.target_db
        while self.replication_ids:
            self.replicator.stop_replication(self.replication_ids.pop())
        del self.replicator
        self.db_tear_down()
        super(ReplicatorTests, self).tearDown()

    def test_constructor(self):
        """
        Test constructing a Replicator
        """
        self.assertIsInstance(self.replicator, Replicator)
        self.assertIsInstance(
            self.replicator.database,
            self.client._DATABASE_CLASS
        )
        self.assertEqual(self.replicator.database, self.client['_replicator'])

    def test_constructor_failure(self):
        """
        Test that constructing a Replicator will not work
        without a valid client.
        """
        repl = None
        try:
            self.client.disconnect()
            repl = Replicator(self.client)
            self.fail('Above statement should raise a CloudantException')
        except CloudantException as err:
            self.assertEqual(
                str(err),
                'Unable to acquire _replicator database.  '
                'Verify that the client is valid and try again.'
            )
        finally:
            self.assertIsNone(repl)
            self.client.connect()

    def test_create_replication(self):
        """
        Test that the replication document gets created and that the
        replication is successful.
        """
        self.populate_db_with_documents(3)
        repl_id = 'test-repl-{}'.format(unicode_(uuid.uuid4()))

        repl_doc = self.replicator.create_replication(
            self.db,
            self.target_db,
            repl_id
        )
        self.replication_ids.append(repl_id)
        # Test that the replication document was created
        expected_keys = ['_id', '_rev', 'source', 'target', 'user_ctx']
        # If Admin Party mode then user_ctx will not be in the key list
        if self.client.admin_party:
            expected_keys.pop()
        self.assertTrue(all(x in list(repl_doc.keys()) for x in expected_keys))
        self.assertEqual(repl_doc['_id'], repl_id)
        self.assertTrue(repl_doc['_rev'].startswith('1-'))
        # Now that we know that the replication document was created,
        # check that the replication occurred.
        repl_doc = Document(self.replicator.database, repl_id)
        repl_doc.fetch()
        if repl_doc.get('_replication_state') not in ('completed', 'error'):
            for change in self.replicator.database.changes():
                if change.get('id') == repl_id:
                    repl_doc = Document(self.replicator.database, repl_id)
                    repl_doc.fetch()
                    if (repl_doc.get('_replication_state')
                        in ('completed', 'error')):
                        break
        self.assertEqual(repl_doc['_replication_state'], 'completed')
        self.assertEqual(self.db.all_docs(), self.target_db.all_docs())
        self.assertTrue(
            all(x in self.target_db.keys(True) for x in [
                'julia000',
                'julia001',
                'julia002'
            ])
        )

    def test_create_replication_without_a_source(self):
        """
        Test that the replication document is not created and fails as expected
        when no source database is provided. 
        """
        try:
            repl_doc = self.replicator.create_replication()
            self.fail('Above statement should raise a CloudantException')
        except CloudantException as err:
            self.assertEqual(
                str(err),
                'You must specify either a source_db Database '
                'object or a manually composed \'source\' string/dict.'
            )

    def test_create_replication_without_a_target(self):
        """
        Test that the replication document is not created and fails as expected
        when no target database is provided. 
        """
        try:
            repl_doc = self.replicator.create_replication(self.db)
            self.fail('Above statement should raise a CloudantException')
        except CloudantException as err:
            self.assertEqual(
                str(err),
                'You must specify either a target_db Database '
                'object or a manually composed \'target\' string/dict.'
            )

    def test_list_replications(self):
        """
        Test that a list of Document wrapped objects are returned.
        """
        self.populate_db_with_documents(3)
        repl_ids = ['test-repl-{}'.format(
            unicode_(uuid.uuid4())
        ) for _ in range(3)]
        repl_docs = [self.replicator.create_replication(
            self.db,
            self.target_db,
            repl_id
        ) for repl_id in repl_ids]
        self.replication_ids.extend(repl_ids)
        replications = self.replicator.list_replications()
        all_repl_ids = [doc['_id'] for doc in replications]
        match = [repl_id for repl_id in all_repl_ids if repl_id in repl_ids]
        self.assertEqual(set(repl_ids), set(match))

    def test_retrieve_replication_state(self):
        """
        Test that the replication state can be retrieved for a replication
        """
        self.populate_db_with_documents(3)
        repl_id = "test-repl-{}".format(unicode_(uuid.uuid4()))
        repl_doc = self.replicator.create_replication(
            self.db,
            self.target_db,
            repl_id
        )
        self.replication_ids.append(repl_id)
        repl_state = None
        valid_states = ['completed', 'error', 'triggered', None]
        finished = False
        for _ in range(300):
            repl_state = self.replicator.replication_state(repl_id)
            self.assertTrue(repl_state in valid_states)
            if repl_state in ('error', 'completed'):
                finished = True
                break
            time.sleep(1)
        self.assertTrue(finished)

    def test_retrieve_replication_state_using_invalid_id(self):
        """
        Test that replication_state(...) raises an exception as expected
        when an invalid replication id is provided.
        """
        repl_id = 'fake-repl-id-{}'.format(unicode_(uuid.uuid4()))
        repl_state = None
        try:
            self.replicator.replication_state(repl_id)
            self.fail('Above statement should raise a CloudantException')
        except CloudantException as err:
            self.assertEqual(
                str(err),
                'Replication {} not found'.format(repl_id)
            )
            self.assertIsNone(repl_state)

    def test_stop_replication(self):
        """
        Test that a replication can be stopped.
        """
        self.populate_db_with_documents(3)
        repl_id = "test-repl-{}".format(unicode_(uuid.uuid4()))
        repl_doc = self.replicator.create_replication(
            self.db,
            self.target_db,
            repl_id
        )
        self.replicator.stop_replication(repl_id)
        try:
            # The .fetch() will fail since the replication has been stopped
            # and the replication document has been removed from the db.
            repl_doc.fetch()
            self.fail('Above statement should raise a CloudantException')
        except requests.HTTPError as err:
            self.assertEqual(err.response.status_code, 404)

    def test_stop_replication_using_invalid_id(self):
        """
        Test that stop_replication(...) raises an exception as expected
        when an invalid replication id is provided.
        """
        repl_id = 'fake-repl-id-{}'.format(unicode_(uuid.uuid4()))
        try:
            self.replicator.stop_replication(repl_id)
            self.fail('Above statement should raise a CloudantException')
        except CloudantException as err:
            self.assertEqual(
                str(err),
                'Could not find replication with id {}'.format(repl_id)
            )

    def test_follow_replication(self):
        """
        Test that follow_replication(...) properly iterates updated
        replication documents while the replication is executing.
        """
        self.populate_db_with_documents(3)
        repl_id = "test-repl-{}".format(unicode_(uuid.uuid4()))
        repl_doc = self.replicator.create_replication(
            self.db,
            self.target_db,
            repl_id
        )
        self.replication_ids.append(repl_id)
        valid_states = ('completed', 'error', 'triggered', None)
        repl_states = []
        for doc in self.replicator.follow_replication(repl_id):
            self.assertIn(doc.get('_replication_state'), valid_states)
            repl_states.append(doc.get('_replication_state'))
        self.assertTrue(len(repl_states) > 0)
        self.assertEqual(repl_states[-1], 'completed')
        self.assertNotIn('error', repl_states)

if __name__ == '__main__':
    unittest.main()
