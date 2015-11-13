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
_replicator_test_

replicator module unit tests

"""

import unittest
import mock
import requests

from cloudant.database import CouchDatabase
from cloudant.errors import CloudantException
from cloudant.replicator import Replicator
from cloudant.document import Document

class ReplicatorTests(unittest.TestCase):
    """
    Tests for Replicator class

    """
    def setUp(self):
        """
        mock out requests.Session
        """
        self.patcher = mock.patch.object(requests, "Session")
        self.mock_session = self.patcher.start()
        self.mock_instance = mock.Mock()
        self.mock_instance.auth = None
        self.mock_instance.headers = {}
        self.mock_instance.cookies = {'AuthSession': 'COOKIE'}
        self.mock_instance.get = mock.Mock()
        self.mock_instance.post = mock.Mock()
        self.mock_instance.delete = mock.Mock()
        self.mock_instance.put = mock.Mock()
        self.mock_session.return_value = self.mock_instance
        self.username = "steve"
        self.password = "abc123"

        self.mock_account = mock.Mock()
        self.mock_account.__getitem__ = mock.Mock()
        self.mock_account.__getitem__.return_value = CouchDatabase(
            self.mock_account,
            '_replicator'
        )
        self.mock_account.session = mock.Mock()
        self.mock_account.session.return_value = {
            "userCtx": "user Context"
        }

    def tearDown(self):
        self.patcher.stop()

    def test_create_replication(self):
        """test create_replication method"""
        with mock.patch('cloudant.database.CouchDatabase.create_document') as mock_create:
            mock_target = mock.Mock()
            mock_target.database_url = "http://bob.cloudant.com/target"
            mock_target.creds = {'basic_auth': "target_auth"}
            mock_source = mock.Mock()
            mock_source.database_url = "http://bob.cloudant.com/source"
            mock_source.creds = {'basic_auth': "source_auth"}

            repl = Replicator(self.mock_account)
            repl.create_replication(mock_source, mock_target, "REPLID")

        self.assertTrue(mock_create.called)
        repl_doc = mock_create.call_args[0][0]
        self.assertTrue('source' in repl_doc)
        self.assertTrue('target' in repl_doc)
        self.assertEqual(repl_doc['_id'], 'REPLID')
        self.assertEqual(
            repl_doc['source']['url'],
            'http://bob.cloudant.com/source'
        )
        self.assertEqual(
            repl_doc['target']['url'],
            'http://bob.cloudant.com/target'
        )
        self.assertEqual(
            repl_doc['target']['headers']['Authorization'],
            'target_auth'
        )
        self.assertEqual(
            repl_doc['source']['headers']['Authorization'],
            'source_auth'
        )

    def test_create_replication_errors(self):
        """check expected error conditions"""
        mock_target = mock.Mock()
        mock_target.database_url = "http://bob.cloudant.com/target"
        mock_target.creds = {'basic_auth': "target_auth"}
        mock_source = mock.Mock()
        mock_source.database_url = "http://bob.cloudant.com/source"
        mock_source.creds = {'basic_auth': "source_auth"}

        repl = Replicator(self.mock_account)
        self.assertRaises(
            CloudantException,
            repl.create_replication,
            target=mock_target,
            repl_id="REPLID"
            )
        self.assertRaises(
            CloudantException,
            repl.create_replication,
            source=mock_source,
            repl_id="REPLID"
            )

    def test_list_replications(self):
        """ test retrieve replications"""
        with mock.patch('cloudant.database.CouchDatabase.all_docs') as mock_all_docs:
            mock_all_docs.return_value = {
                "rows": [
                    {"id": "replication_1", "doc": {"_id": "replication_1"}},
                    {"id": "replication_2", "doc": {"_id": "replication_2"}}
                ]
            }
            repl = Replicator(self.mock_account)

            self.assertEqual(
                repl.list_replications(),
                [{"_id": "replication_1"}, {"_id": "replication_2"}]
            )

    def test_replication_state(self):
        """test replication state method"""
        repl = Replicator(self.mock_account)

        mock_doc = mock.Mock()
        mock_doc.fetch = mock.Mock()
        mock_doc.get = mock.Mock()
        mock_doc.get.return_value = "STATE"

        repl.database['replication_1'] = mock_doc
        self.assertEqual(repl.replication_state('replication_1'), 'STATE')

        with mock.patch('cloudant.database.CouchDatabase.__getitem__') as mock_gi:
            mock_gi.side_effect = KeyError("womp")
            self.assertRaises(
                CloudantException,
                repl.replication_state,
                'replication_2'
            )

    def test_stop_replication(self):
        """test stop_replication call"""
        repl = Replicator(self.mock_account)

        mock_doc = mock.Mock()
        mock_doc.fetch = mock.Mock()
        mock_doc.delete = mock.Mock()

        repl.database['replication_1'] = mock_doc
        repl.stop_replication('replication_1')
        self.assertTrue(mock_doc.fetch.called)
        self.assertTrue(mock_doc.delete.called)

        with mock.patch('cloudant.database.CouchDatabase.__getitem__') as mock_gi:
            mock_gi.side_effect = KeyError("womp")
            self.assertRaises(
                CloudantException,
                repl.stop_replication,
                'replication_2'
            )

    def test_follow_replication(self):
        """test follow replication feature"""
        with mock.patch('cloudant.database.CouchDatabase.changes') as mock_changes:
            mock_changes.return_value = [
                {"id": "not_this replication"},
                {"id": "not_this replication"},
                {"id": "replication_1", "_replication_state": "not finished"},
                {"id": "replication_1", "_replication_state": "completed"},
            ]
            repl = Replicator(self.mock_account)

            mock_doc = mock.Mock()
            mock_doc.fetch = mock.Mock()
            mock_doc.get = mock.Mock()
            mock_doc.get.side_effect = ['triggered', 'triggered', 'triggered', 'completed']

            repl.database['replication_1'] = mock_doc

            for x, i in enumerate(repl.follow_replication('replication_1')):
                pass
            # expect 4 iterations
            self.assertEqual(x, 3)

if __name__ == '__main__':
    unittest.main()
