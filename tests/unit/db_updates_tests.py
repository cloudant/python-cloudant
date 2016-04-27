#!/usr/bin/env python
# Copyright (c) 2016 IBM. All rights reserved.
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
Unit tests for _db_updates feed
"""

import unittest
from requests import Session
import json
import os

from cloudant.feed import Feed
from cloudant.document import Document
from cloudant.design_document import DesignDocument
from cloudant.error import CloudantArgumentError, CloudantException
from cloudant._2to3 import unicode_

from .unit_t_db_base import UnitTestDbBase
from .. import BYTETYPE

class DbUpdatesTestsBase(UnitTestDbBase):
    """
    Common _db_updates tests methods
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(DbUpdatesTestsBase, self).setUp()
        self.client.connect()
        self.new_dbs = list()

    def tearDown(self):
        """
        Reset test attributes
        """
        [db.delete() for db in self.new_dbs]
        self.client.disconnect()
        super(DbUpdatesTestsBase, self).tearDown()

    def create_dbs(self, count=3):
        self.new_dbs += [(self.client.create_database(self.dbname())) for x in range(count)]

@unittest.skipIf(os.environ.get('RUN_CLOUDANT_TESTS'),
    'Skipping CouchDB _db_updates feed tests')
class CouchDbUpdatesTests(DbUpdatesTestsBase):
    """
    CouchDB _db_updates feed unit tests
    """
    def test_constructor_db_updates(self):
        """
        Test constructing a _db_updates feed
        """
        feed = Feed(self.client, feed='continuous', heartbeat=False, timeout=2)
        self.assertEqual(feed._url,
            '/'.join([self.client.cloudant_url, '_db_updates']))
        self.assertIsInstance(feed._r_session, Session)
        self.assertFalse(feed._raw_data)
        self.assertDictEqual(feed._options,
            {'feed': 'continuous', 'heartbeat': False, 'timeout': 2})

    def test_stop_iteration_of_continuous_feed_with_heartbeat(self):
        """
        Test stopping the iteration, test a continuous feed, and test
        heartbeat functionality.
        """
        feed = Feed(self.client, feed='continuous', timeout=100)
        changes = list()
        for change in feed:
            if not change:
                if not self.new_dbs:
                    self.create_dbs(5)
                else:
                    continue
            else:
                changes.append(change)
                if len(changes) == 3:
                    feed.stop()
        self.assertEqual(len(self.new_dbs), 5)
        self.assertEqual(len(changes), 3)
        self.assertDictEqual(
            changes[0], {'db_name': self.new_dbs[0].database_name, 'type': 'created'})
        self.assertDictEqual(
            changes[1], {'db_name': self.new_dbs[1].database_name, 'type': 'created'})
        self.assertDictEqual(
            changes[2], {'db_name': self.new_dbs[2].database_name, 'type': 'created'})

    def test_get_raw_content(self):
        """
        Test getting raw feed content
        """
        feed = Feed(self.client, raw_data='True', feed='continuous', timeout=100)
        raw_content = list()
        for raw_line in feed:
            self.assertIsInstance(raw_line, BYTETYPE)
            if not raw_line:
                self.create_dbs(3)
            else:
                raw_content.append(raw_line)
                if len(raw_content) == 3:
                    feed.stop()
        changes = [json.loads(unicode_(x)) for x in raw_content]
        self.assertDictEqual(
            changes[0], {'db_name': self.new_dbs[0].database_name, 'type': 'created'})
        self.assertDictEqual(
            changes[1], {'db_name': self.new_dbs[1].database_name, 'type': 'created'})
        self.assertDictEqual(
            changes[2], {'db_name': self.new_dbs[2].database_name, 'type': 'created'})

    def test_get_longpoll_feed_as_default(self):
        """
        Test getting content back for a "longpoll" feed
        """
        feed = Feed(self.client, timeout=1000)
        changes = list()
        for change in feed:
            self.assertIsNone(change)
            changes.append(change)
        self.assertEqual(len(changes), 1)
        self.assertIsNone(changes[0])

    def test_get_longpoll_feed_explicit(self):
        """
        Test getting content back for a "longpoll" feed while setting feed to
        longpoll explicitly
        """
        feed = Feed(self.client, timeout=1000, feed='longpoll')
        changes = list()
        for change in feed:
            self.assertIsNone(change)
            changes.append(change)
        self.assertEqual(len(changes), 1)
        self.assertIsNone(changes[0])

    def test_get_continuous_with_timeout(self):
        """
        Test getting content back for a "continuous" feed with timeout set
        and no heartbeat
        """
        feed = Feed(self.client, feed='continuous', heartbeat=False, timeout=1000)
        self.assertListEqual([x for x in feed], [])

    def test_invalid_argument(self):
        """
        Test that an invalid argument is caught and an exception is raised
        """
        feed = Feed(self.client, foo='bar')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(str(cm.exception), 'Invalid argument foo')

        feed = Feed(self.client, style='all_docs')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(str(cm.exception), 'Invalid argument style')

        feed = Feed(self.client, descending=True)
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(str(cm.exception), 'Invalid argument descending')

    def test_invalid_argument_type(self):
        """
        Test that an invalid argument type is caught and an exception is raised
        """
        feed = Feed(self.client, heartbeat=6)
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertTrue(
            str(cm.exception).startswith(
                'Argument heartbeat not instance of expected type:')
        )

    def test_invalid_non_positive_integer_argument(self):
        """
        Test that an invalid integer argument type is caught and an exception is
        raised
        """
        feed = Feed(self.client, timeout=-1)
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(
            str(cm.exception), 'Argument timeout must be > 0.  Found: -1')

    def test_invalid_feed_value(self):
        """
        Test that an invalid feed argument value is caught and an exception is
        raised
        """
        feed = Feed(self.client, feed='foo')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertTrue(str(cm.exception).startswith(
            'Invalid value (foo) for feed option.'))

        feed = Feed(self.client, feed='normal')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertTrue(str(cm.exception).startswith(
            'Invalid value (normal) for feed option.'))

@unittest.skipIf(not os.environ.get('RUN_CLOUDANT_TESTS') or
    os.environ.get('SKIP_DB_UPDATES'), 'Skipping Cloudant _db_updates feed tests')
class CloudantDbUpdatesTests(DbUpdatesTestsBase):
    """
    Cloudant _db_updates feed unit tests
    """

    def test_constructor_db_updates(self):
        """
        Test constructing a _db_updates feed
        """
        feed = Feed(self.client, feed='continuous', heartbeat=5000)
        self.assertEqual(feed._url,
            '/'.join([self.client.cloudant_url, '_db_updates']))
        self.assertIsInstance(feed._r_session, Session)
        self.assertFalse(feed._raw_data)
        self.assertDictEqual(feed._options,
            {'feed': 'continuous', 'heartbeat': 5000})

    def test_get_last_seq(self):
        """
        Test getting the last sequence identifier
        """
        self.create_dbs(1)
        feed = Feed(self.client, since='now')
        self.assertIsNone(feed.last_seq)
        [x for x in feed]
        self.assertIsNotNone(feed.last_seq)

    def test_stop_iteration_of_continuous_feed_using_since_now(self):
        """
        Test stopping the iteration, test continuous feed functionality, test
        using since='now' option.
        """
        feed = Feed(self.client, feed='continuous', since='now')
        count = 0
        changes = list()
        self.create_dbs(3)
        for change in feed:
            self.assertTrue(all(x in change for x in ('seq', 'type')))
            changes.append(change)
            count += 1
            if count == 2:
                feed.stop()
        self.assertEqual(len(changes), 2)
        self.assertTrue(changes[0]['seq'] < changes[1]['seq'])
        self.assertIsNone(feed.last_seq)

    def test_get_raw_content(self):
        """
        Test getting raw feed content
        """
        self.create_dbs(3)
        feed = Feed(self.client, limit=3, raw_data=True)
        raw_content = list()
        for raw_line in feed:
            self.assertIsInstance(raw_line, BYTETYPE)
            raw_content.append(raw_line)
        changes = json.loads(''.join([unicode_(x) for x in raw_content]))
        self.assertSetEqual(set(changes.keys()), set(['results', 'last_seq']))
        self.assertEqual(len(changes['results']), 3)
        self.assertIsNotNone(changes['last_seq'])
        self.assertIsNone(feed.last_seq)

    def test_get_normal_feed_default(self):
        """
        Test getting content back for a "normal" feed without feed option.  Also
        using limit since we don't know how many updates have occurred on client.
        """
        self.create_dbs(3)
        feed = Feed(self.client, limit=3)
        changes = list()
        for change in feed:
            self.assertTrue(all(x in change for x in ('seq', 'type')))
            changes.append(change)
        self.assertEqual(len(changes), 3)
        self.assertTrue(changes[0]['seq'] < changes[1]['seq'] < changes[2]['seq'])
        self.assertIsNotNone(feed.last_seq)

    def test_get_normal_feed_explicit(self):
        """
        Test getting content back for a "normal" feed using feed option.  Also
        using limit since we don't know how many updates have occurred on client.
        """
        self.create_dbs(3)
        feed = Feed(self.client, feed='normal', limit=3)
        changes = list()
        for change in feed:
            self.assertTrue(all(x in change for x in ('seq', 'type')))
            changes.append(change)
        self.assertEqual(len(changes), 3)
        self.assertTrue(changes[0]['seq'] < changes[1]['seq'] < changes[2]['seq'])
        self.assertIsNotNone(feed.last_seq)

    def test_get_longpoll_feed(self):
        """
        Test getting content back for a "longpoll" feed
        """
        self.create_dbs(3)
        feed = Feed(self.client, feed='longpoll', limit=3)
        changes = list()
        for change in feed:
            self.assertTrue(all(x in change for x in ('seq', 'type')))
            changes.append(change)
        self.assertEqual(len(changes), 3)
        self.assertIsNotNone(feed.last_seq)

    def test_get_feed_with_heartbeat(self):
        """
        Test getting content back for a feed with a heartbeat
        """
        feed = Feed(self.client, feed='continuous', since='now', heartbeat=1000)
        changes = list()
        heartbeats = 0
        for change in feed:
            if not change:
                self.assertIsNone(change)
                heartbeats += 1
                if heartbeats < 4:
                    self.create_dbs(1)
            else:
                self.assertTrue(all(x in change for x in ('seq', 'type')))
                if len(changes) < 3:
                    changes.append(change)
            if heartbeats >= 3 and len(changes) == 3:
                feed.stop()
        self.assertTrue(changes[0]['seq'] < changes[1]['seq'] < changes[2]['seq'])
        self.assertIsNone(feed.last_seq)

    def test_get_raw_feed_with_heartbeat(self):
        """
        Test getting raw content back for a feed with a heartbeat
        """
        feed = Feed(self.client, raw_data=True, feed='continuous', since='now',
            heartbeat=1000)
        raw_content = list()
        heartbeats = 0
        for raw_line in feed:
            if not raw_line:
                self.assertEqual(len(raw_line), 0)
                heartbeats += 1
                if heartbeats < 4:
                    self.create_dbs(1)
            else:
                self.assertIsInstance(raw_line, BYTETYPE)
                raw_content.append(raw_line) 
            if heartbeats >= 3 and len(raw_content) >= 3:
                feed.stop()
        changes = [json.loads(unicode_(x)) for x in raw_content]
        self.assertTrue(changes[0]['seq'] < changes[1]['seq'] < changes[2]['seq'])
        self.assertIsNone(feed.last_seq)

    def test_get_feed_descending(self):
        """
        Test getting content back for a descending feed.
        """
        self.create_dbs(3)
        feed = Feed(self.client, limit=3, descending=True)
        changes = list()
        for change in feed:
            self.assertTrue(all(x in change for x in ('seq', 'type')))
            changes.append(change)
        self.assertEqual(len(changes), 3)
        self.assertTrue(changes[0]['seq'] > changes[1]['seq'] > changes[2]['seq'])
        self.assertIsNotNone(feed.last_seq)

    def test_get_feed_using_since(self):
        """
        Test getting content back for a feed using the since option
        """
        self.create_dbs(1)
        feed = Feed(self.client, since='now')
        [x for x in feed]
        last_seq = feed.last_seq
        self.create_dbs(3)
        feed = Feed(self.client, since=last_seq)
        for change in feed:
            self.assertTrue(all(x in change for x in ('seq', 'type')))
        self.assertTrue(feed.last_seq > last_seq)

    def test_get_feed_using_timeout(self):
        """
        Test getting content back for a feed using timeout.  Since we do not
        have control over updates happening within the account as we do within a
        database, this test is stopped after 15 changes are received which
        should theoretically not happen but we still need a way to break out of
        the test if necessary.
        """
        feed = Feed(self.client, feed='continuous', since='now', timeout=1000)
        count = 0
        self.create_dbs(1)
        for change in feed:
            self.assertTrue(all(x in change for x in ('seq', 'type')))
            count += 1
            if count == 15:
                feed.stop()
        # The test is considered a success if the last_seq value exists on the
        # feed object.  One would not exist if the feed was stopped via .stop().
        # If failure occurs it does not necessarily mean that the InfiniteFeed
        # is not functioning as expected, it might also mean that we reached the
        # changes limit threshold of 15 before a timeout could happen.
        self.assertIsNotNone(feed.last_seq)

    def test_invalid_argument(self):
        """
        Test that an invalid argument is caught and an exception is raised
        """
        feed = Feed(self.client, foo='bar')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(str(cm.exception), 'Invalid argument foo')

        feed = Feed(self.client, style='all_docs')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(str(cm.exception), 'Invalid argument style')

    def test_invalid_argument_type(self):
        """
        Test that an invalid argument type is caught and an exception is raised
        """
        feed = Feed(self.client, descending=6)
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertTrue(
            str(cm.exception).startswith(
                'Argument descending not instance of expected type:')
        )

    def test_invalid_non_positive_integer_argument(self):
        """
        Test that an invalid integer argument type is caught and an exception is
        raised
        """
        feed = Feed(self.client, limit=-1)
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(
            str(cm.exception), 'Argument limit must be > 0.  Found: -1')

    def test_invalid_feed_value(self):
        """
        Test that an invalid feed argument value is caught and an exception is
        raised
        """
        feed = Feed(self.client, feed='foo')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertTrue(str(cm.exception).startswith(
            'Invalid value (foo) for feed option.'))

if __name__ == '__main__':
    unittest.main()
