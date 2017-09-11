#!/usr/bin/env python
# Copyright (c) 2015, 2016, 2017 IBM Corp. All rights reserved.
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

from flaky import flaky
import requests
from requests import ConnectionError

from cloudant.replicator import Replicator
from cloudant.document import Document
from cloudant.error import CloudantReplicatorException, CloudantClientException

from .unit_t_db_base import skip_for_iam, UnitTestDbBase
from .. import unicode_

class CloudantReplicatorExceptionTests(unittest.TestCase):
    """
    Ensure CloudantReplicatorException functions as expected.
    """

    def test_raise_without_code(self):
        """
        Ensure that a default exception/code is used if none is provided.
        """
        with self.assertRaises(CloudantReplicatorException) as cm:
            raise CloudantReplicatorException()
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_using_invalid_code(self):
        """
        Ensure that a default exception/code is used if invalid code is provided.
        """
        with self.assertRaises(CloudantReplicatorException) as cm:
            raise CloudantReplicatorException('foo')
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_without_args(self):
        """
        Ensure that a default exception/code is used if the message requested
        by the code provided requires an argument list and none is provided.
        """
        with self.assertRaises(CloudantReplicatorException) as cm:
            raise CloudantReplicatorException(404)
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_with_proper_code_and_args(self):
        """
        Ensure that the requested exception is raised.
        """
        with self.assertRaises(CloudantReplicatorException) as cm:
            raise CloudantReplicatorException(404, 'foo')
        self.assertEqual(cm.exception.status_code, 404)

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

        for rep_id in self.replication_ids:
            max_retry = 5
            while True:
                try:
                    self.replicator.stop_replication(rep_id)
                    break

                except requests.HTTPError as ex:
                    # Retry failed attempt to delete replication document. It's
                    # likely in an error state and receiving constant updates
                    # via the replicator.
                    max_retry -= 1
                    if ex.response.status_code != 409 or max_retry == 0:
                        raise

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
        except CloudantClientException as err:
            self.assertEqual(
                str(err),
                'Database _replicator does not exist. '
                'Verify that the client is valid and try again.'
            )
        finally:
            self.assertIsNone(repl)
            self.client.connect()

    def test_replication_with_generated_id(self):
        clone = Replicator(self.client)
        clone.create_replication(self.db, self.target_db)

    @skip_for_iam
    @flaky(max_runs=3)
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
            changes = self.replicator.database.changes(
                feed='continuous',
                heartbeat=1000)
            beats = 0
            for change in changes:
                if beats == 300:
                    changes.stop()
                if not change:
                    beats += 1
                    continue
                elif change.get('id') == repl_id:
                    beats = 0
                    repl_doc = Document(self.replicator.database, repl_id)
                    repl_doc.fetch()
                    if repl_doc.get('_replication_state') in ('completed', 'error'):
                        changes.stop()
        self.assertEqual(repl_doc.get('_replication_state'), 'completed')
        self.assertEqual(self.db.all_docs(), self.target_db.all_docs())
        self.assertTrue(
            all(x in self.target_db.keys(True) for x in [
                'julia000',
                'julia001',
                'julia002'
            ])
        )

    def test_timeout_in_create_replication(self):
        """
        Test that a read timeout exception is thrown when creating a
        replicator with a timeout value of 500 ms.
        """
        # Setup client with a timeout
        self.set_up_client(auto_connect=True, timeout=.5)
        self.db = self.client[self.test_target_dbname]
        self.target_db = self.client[self.test_dbname]
        # Construct a replicator with the updated client
        self.replicator = Replicator(self.client)

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
        # check that the replication timed out.
        repl_doc = Document(self.replicator.database, repl_id)
        repl_doc.fetch()
        if repl_doc.get('_replication_state') not in ('completed', 'error'):
            # assert that a connection error is thrown because the read timed out
            with self.assertRaises(ConnectionError) as cm:
                changes = self.replicator.database.changes(
                    feed='continuous')
                for change in changes:
                    continue
            self.assertTrue(str(cm.exception).endswith('Read timed out.'))

    def test_create_replication_without_a_source(self):
        """
        Test that the replication document is not created and fails as expected
        when no source database is provided. 
        """
        try:
            repl_doc = self.replicator.create_replication()
            self.fail('Above statement should raise a CloudantException')
        except CloudantReplicatorException as err:
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
        except CloudantReplicatorException as err:
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

    @skip_for_iam
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
        except CloudantReplicatorException as err:
            self.assertEqual(
                str(err),
                'Replication with id {} not found.'.format(repl_id)
            )
            self.assertIsNone(repl_state)

    @skip_for_iam
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
        except CloudantReplicatorException as err:
            self.assertEqual(
                str(err),
                'Replication with id {} not found.'.format(repl_id)
            )

    @skip_for_iam
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
