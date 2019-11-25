#!/usr/bin/env python
# Copyright (C) 2016, 2018 IBM Corp. All rights reserved.
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
feed module - Unit tests for Feed class
"""

import os
import unittest
from time import sleep

from cloudant.error import CloudantArgumentError, CloudantFeedException
from cloudant.feed import InfiniteFeed, Feed
from nose.plugins.attrib import attr
from requests import Session

from .unit_t_db_base import UnitTestDbBase


class MethodCallCount(object):
    """
    This callable class is used as a proxy by the infinite feed tests to wrap
    method calls with the intent of tracking the number of times a specific
    method has been called.
    """
    def __init__(self, meth_ref):
        self._ref = meth_ref
        self.called_count = 0

    def __call__(self):
        self.called_count += 1
        self._ref()

class CloudantFeedExceptionTests(unittest.TestCase):
    """
    Ensure CloudantFeedException functions as expected.
    """

    def test_raise_without_code(self):
        """
        Ensure that a default exception/code is used if none is provided.
        """
        with self.assertRaises(CloudantFeedException) as cm:
            raise CloudantFeedException()
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_using_invalid_code(self):
        """
        Ensure that a default exception/code is used if invalid code is provided.
        """
        with self.assertRaises(CloudantFeedException) as cm:
            raise CloudantFeedException('foo')
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_with_proper_code_and_args(self):
        """
        Ensure that the requested exception is raised.
        """
        with self.assertRaises(CloudantFeedException) as cm:
            raise CloudantFeedException(101)
        self.assertEqual(cm.exception.status_code, 101)

@attr(db=['cloudant','couch'])
class InfiniteFeedTests(UnitTestDbBase):
    """
    Infinite Feed unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(InfiniteFeedTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(InfiniteFeedTests, self).tearDown()

    def test_constructor_no_feed_option(self):
        """
        Test constructing an infinite feed when no feed option is set
        """
        feed = InfiniteFeed(self.db, chunk_size=1, timeout=100)
        self.assertEqual(feed._url, '/'.join([self.db.database_url, '_changes']))
        self.assertIsInstance(feed._r_session, Session)
        self.assertFalse(feed._raw_data)
        self.assertDictEqual(feed._options, {'feed': 'continuous', 'timeout': 100})
        self.assertEqual(feed._chunk_size, 1)

    def test_constructor_with_feed_option(self):
        """
        Test constructing an infinite feed when the continuous feed
        option is set.
        """
        feed = InfiniteFeed(self.db, chunk_size=1, timeout=100, feed='continuous')
        self.assertEqual(feed._url, '/'.join([self.db.database_url, '_changes']))
        self.assertIsInstance(feed._r_session, Session)
        self.assertFalse(feed._raw_data)
        self.assertDictEqual(feed._options, {'feed': 'continuous', 'timeout': 100})
        self.assertEqual(feed._chunk_size, 1)

    def test_constructor_with_invalid_feed_option(self):
        """
        Test constructing an infinite feed when a feed option is set
        to an invalid value raises an exception.
        """
        feed = InfiniteFeed(self.db, feed='longpoll')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(
            str(cm.exception),
            'Invalid infinite feed option: longpoll.  Must be set to continuous.'
        )

    @attr(db='couch')
    def test_invalid_source_couchdb(self):
        """
        Ensure that a CouchDB client cannot be used with an infinite feed.
        """
        with self.assertRaises(CloudantFeedException) as cm:
            invalid_feed = [x for x in InfiniteFeed(self.client)]
        self.assertEqual(str(cm.exception),
            'Infinite _db_updates feed not supported for CouchDB.')
    
    @unittest.skipIf(os.environ.get('SKIP_DB_UPDATES'), 'Skipping Cloudant _db_updates feed tests')
    @attr(db='cloudant')
    def test_constructor_db_updates(self):
        """
        Test constructing an infinite _db_updates feed.
        """
        feed = InfiniteFeed(self.client, chunk_size=1, timeout=100, feed='continuous')
        self.assertEqual(feed._url, '/'.join([self.client.server_url, '_db_updates']))
        self.assertIsInstance(feed._r_session, Session)
        self.assertFalse(feed._raw_data)
        self.assertDictEqual(feed._options, {'feed': 'continuous', 'timeout': 100})
        self.assertEqual(feed._chunk_size, 1)

    def test_infinite_feed(self):
        """
        Test that an infinite feed will continue to issue multiple requests
        until stopped.  This check is performed in combination by creating
        documents 3 separate times and checking that the "_start" method on the
        InfiniteFeed object was called 3 times as well.
        """
        self.populate_db_with_documents()
        feed = InfiniteFeed(self.db, timeout=100)

        # Create a proxy for the feed._start method so that we can track how
        # many times it has been called.
        feed._start = MethodCallCount(feed._start)

        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
            if len(changes) in (100, 200):
                sleep(1) # 1 second > .1 second (timeout)
                self.populate_db_with_documents(off_set=len(changes))
            elif len(changes) == 300:
                feed.stop()
        expected = set(['julia{0:03d}'.format(i) for i in range(300)])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertIsNone(feed.last_seq)
        # Compare infinite/continuous with normal
        normal = Feed(self.db)
        self.assertSetEqual(
            set([x['id'] for x in changes]), set([n['id'] for n in normal]))

        # Ensuring that the feed._start method was called 3 times, verifies that
        # the continuous feed was started/restarted 3 separate times.
        self.assertEqual(feed._start.called_count, 3)

    @unittest.skipIf(os.environ.get('SKIP_DB_UPDATES'), 'Skipping Cloudant _db_updates feed tests')
    @attr(db='cloudant')
    def test_infinite_db_updates_feed(self):
        """
        Test that an _db_updates infinite feed will continue to issue multiple
        requests until stopped.  Since we do not have control over updates
        happening within the account as we do within a database, this test is
        stopped after 15 database creations regardless.  Within that span of
        time we expect that the feed would have been restarted at least once.

        """
        feed = InfiniteFeed(self.client, since='now', timeout=100)

        # Create a proxy for the feed._start method so that we can track how
        # many times it has been called.
        feed._start = MethodCallCount(feed._start)

        new_dbs = list()
        try:
            new_dbs.append(self.client.create_database(self.dbname()))
            for change in feed:
                self.assertTrue(all(x in change for x in ('seq', 'type')))
                new_dbs.append(self.client.create_database(self.dbname()))
                if feed._start.called_count >= 3 and len(new_dbs) >= 3:
                    feed.stop()
                if len(new_dbs) >= 15:
                    # We stop regardless after 15 databases have been created
                    feed.stop()
        finally:
            [db.delete() for db in new_dbs]
        # The test is considered a success if feed._start was called 2+ times.
        # If failure occurs it does not necessarily mean that the InfiniteFeed
        # is not functioning as expected, it might also mean that we reached the
        # db limit threshold of 15 before a timeout and restart of the
        # InfiniteFeed could happen.
        self.assertTrue(feed._start.called_count > 1)

if __name__ == '__main__':
    unittest.main()
