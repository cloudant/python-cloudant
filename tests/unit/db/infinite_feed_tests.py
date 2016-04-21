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
feed module - Unit tests for Feed class
"""

import unittest
from requests import Session
import json
import os
from time import sleep

from cloudant.feed import InfiniteFeed, Feed
from cloudant.error import CloudantArgumentError

from .unit_t_db_base import UnitTestDbBase

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
        self.changes_url = '/'.join([self.db.database_url, '_changes'])
        self.session = self.client.r_session

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(InfiniteFeedTests, self).tearDown()

    def test_constructor_no_feed_option(self):
        """
        Test constructing an infinite _changes feed when no feed option is set
        """
        feed = InfiniteFeed(self.session, self.changes_url, chunk_size=1,
            timeout=100)
        self.assertEqual(feed._url, self.changes_url)
        self.assertIsInstance(feed._r_session, Session)
        self.assertFalse(feed._raw_data)
        self.assertDictEqual(feed._options, {'feed': 'continuous', 'timeout': 100})
        self.assertEqual(feed._chunk_size, 1)

    def test_constructor_with_feed_option(self):
        """
        Test constructing an infinite _changes feed when the continuous feed
        option is set.
        """
        feed = InfiniteFeed(self.session, self.changes_url, chunk_size=1,
            timeout=100, feed='continuous')
        self.assertEqual(feed._url, self.changes_url)
        self.assertIsInstance(feed._r_session, Session)
        self.assertFalse(feed._raw_data)
        self.assertDictEqual(feed._options, {'feed': 'continuous', 'timeout': 100})
        self.assertEqual(feed._chunk_size, 1)

    def test_constructor_with_invalid_feed_option(self):
        """
        Test constructing an infinite _changes feed when a feed option is set
        to an invalid value raises an exception.
        """
        feed = InfiniteFeed(self.session, self.changes_url, feed='longpoll')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(str(cm.exception), 
            'Invalid infinite feed option: longpoll.  Must be set to continuous.')

    def test_infinite_feed(self):
        """
        Test that an infinite feed will continue to issue multiple requests
        until stopped.  This check is performed in combination by creating
        documents 3 separate times and checking that the "_start" method on the
        InfiniteFeed object was called 3 times as well.
        """
        
        # Method proxy callable class
        class MethodCallCount(object):
            def __init__(self, meth_ref):
                self._ref = meth_ref
                self.called_count = 0

            def __call__(self):
                self.called_count += 1
                self._ref()

        self.populate_db_with_documents()
        feed = InfiniteFeed(self.session, self.changes_url, timeout=100)

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
        normal = Feed(self.session, self.changes_url)
        self.assertSetEqual(
            set([x['id'] for x in changes]), set([n['id'] for n in normal]))

        # Ensuring that the feed._start method was called 3 times, verifies that
        # the continuous feed was started/restarted 3 separate times.
        self.assertEqual(feed._start.called_count, 3)

if __name__ == '__main__':
    unittest.main()
