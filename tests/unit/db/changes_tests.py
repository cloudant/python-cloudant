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
Unit tests for _changes feed
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
from ... import BYTETYPE

class ChangesTests(UnitTestDbBase):
    """
    _changes feed unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(ChangesTests, self).setUp()
        self.db_set_up()
        self.cloudant_test = os.environ.get('RUN_CLOUDANT_TESTS') is not None

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(ChangesTests, self).tearDown()

    def test_constructor_changes(self):
        """
        Test constructing a _changes feed
        """
        feed = Feed(self.db, raw_data=True, chunk_size=1, feed='continuous')
        self.assertEqual(feed._url, '/'.join([self.db.database_url, '_changes']))
        self.assertIsInstance(feed._r_session, Session)
        self.assertTrue(feed._raw_data)
        self.assertDictEqual(feed._options, {'feed': 'continuous'})
        self.assertEqual(feed._chunk_size, 1)

    def test_get_last_seq(self):
        """
        Test getting the last sequence identifier
        """
        self.populate_db_with_documents(10)
        feed = Feed(self.db)
        changes = [x for x in feed]
        self.assertTrue(str(feed.last_seq).startswith('10'))

    def test_stop_iteration(self):
        """
        Test stopping the iteration
        """
        self.populate_db_with_documents(10)
        feed = Feed(self.db, feed='continuous')
        count = 0
        changes = list()
        for change in feed:
            changes.append(change)
            count += 1
            if count == 3:
                feed.stop()
        self.assertEqual(len(change), 3)
        self.assertTrue(str(changes[0]['seq']).startswith('1'))
        self.assertTrue(str(changes[1]['seq']).startswith('2'))
        self.assertTrue(str(changes[2]['seq']).startswith('3'))
        self.assertIsNone(feed.last_seq)

    def test_get_raw_content(self):
        """
        Test getting raw feed content
        """
        self.populate_db_with_documents(3)
        feed = Feed(self.db, raw_data=True)
        raw_content = list()
        for raw_line in feed:
            self.assertIsInstance(raw_line, BYTETYPE)
            raw_content.append(raw_line)
        changes = json.loads(''.join([unicode_(x) for x in raw_content]))
        if self.cloudant_test:
            self.assertSetEqual(
                set(changes.keys()), set(['results', 'last_seq', 'pending']))
        else:
            self.assertSetEqual(
                set(changes.keys()), set(['results', 'last_seq']))
        results = list()
        for result in changes['results']:
            self.assertSetEqual(set(result.keys()), set(['seq', 'changes', 'id']))
            results.append(result)
        expected = set(['julia000', 'julia001', 'julia002'])
        self.assertSetEqual(set([x['id'] for x in results]), expected)
        self.assertTrue(str(changes['last_seq']).startswith('3'))
        self.assertIsNone(feed.last_seq)

    def test_get_normal_feed_default(self):
        """
        Test getting content back for a "normal" feed without feed option
        """
        self.populate_db_with_documents(3)
        feed = Feed(self.db)
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
        expected = set(['julia000', 'julia001', 'julia002'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('3'))

    def test_get_normal_feed_explicit(self):
        """
        Test getting content back for a "normal" feed using feed option
        """
        self.populate_db_with_documents(3)
        feed = Feed(self.db, feed='normal')
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
        expected = set(['julia000', 'julia001', 'julia002'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('3'))

    def test_get_continuous_feed(self):
        """
        Test getting content back for a "continuous" feed
        """
        self.populate_db_with_documents()
        feed = Feed(self.db, feed='continuous')
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
            if len(changes) == 100:
                feed.stop()
        expected = set(['julia{0:03d}'.format(i) for i in range(100)])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertIsNone(feed.last_seq)
        # Compare continuous with normal
        normal = Feed(self.db)
        self.assertSetEqual(
            set([x['id'] for x in changes]), set([n['id'] for n in normal]))

    def test_get_longpoll_feed(self):
        """
        Test getting content back for a "longpoll" feed
        """
        feed = Feed(self.db, feed='longpoll', heartbeat=10)
        changes = list()
        for change in feed:
            if not change:
                self.populate_db_with_documents(1)
                continue
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
        self.assertListEqual([x['id'] for x in changes], ['julia000'])
        self.assertTrue(str(feed.last_seq).startswith('1'))

    def test_get_feed_with_heartbeat(self):
        """
        Test getting content back for a feed with a heartbeat
        """
        self.populate_db_with_documents()
        feed = Feed(self.db, feed='continuous', heartbeat=10)
        changes = list()
        heartbeats = 0
        for change in feed:
            if not change:
                self.assertIsNone(change)
                heartbeats += 1
            else:
                self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
                changes.append(change)
            if heartbeats == 3:
                feed.stop()
        expected = set(['julia{0:03d}'.format(i) for i in range(100)])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertIsNone(feed.last_seq)

    def test_get_raw_feed_with_heartbeat(self):
        """
        Test getting raw content back for a feed with a heartbeat
        """
        self.populate_db_with_documents()
        feed = Feed(self.db, raw_data=True, feed='continuous', heartbeat=10)
        raw_content = list()
        heartbeats = 0
        for raw_line in feed:
            if not raw_line:
                self.assertEqual(len(raw_line), 0)
                heartbeats += 1
            else:
                self.assertIsInstance(raw_line, BYTETYPE)
                raw_content.append(raw_line)
            if heartbeats == 3:
                feed.stop()
        changes = [json.loads(unicode_(x)) for x in raw_content]
        expected = set(['julia{0:03d}'.format(i) for i in range(100)])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertIsNone(feed.last_seq)

    def test_get_feed_descending(self):
        """
        Test getting content back for a descending feed.  When testing with
        Cloudant the sequence identifier is in the form of 
        <number prefix>-<random char seq>.  Often times the number prefix sorts
        as expected when using descending but sometimes the number prefix is
        repeated.  In these cases the check is to see if the following random
        character sequence suffix is longer than its predecessor.
        """
        self.populate_db_with_documents(50)
        feed = Feed(self.db, descending=True)
        seq_list = list()
        last_seq = None
        for change in feed:
            if last_seq:
                if self.cloudant_test:
                    current = int(change['seq'][0: change['seq'].find('-')])
                    last = int(last_seq[0:last_seq.find('-')])
                    try:
                        self.assertTrue(current < last)
                    except AssertionError:
                        self.assertEqual(current, last)
                        self.assertTrue(len(change['seq']) > len(last_seq))
                else:
                    self.assertTrue(change['seq'] < last_seq)
            seq_list.append(change['seq'])
            last_seq = change['seq']
        self.assertEqual(len(seq_list), 50)
        self.assertEqual(feed.last_seq, last_seq)

    def test_get_feed_include_docs(self):
        """
        Test getting content back for a feed that includes documents
        """
        self.populate_db_with_documents(3)
        feed = Feed(self.db, include_docs=True)
        ids = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id', 'doc']))
            self.assertSetEqual(
                set(change['doc'].keys()), set(['_id', '_rev', 'name', 'age']))
            ids.append(change['id'])
        self.assertSetEqual(set(ids), set(['julia000', 'julia001', 'julia002']))

    def test_get_feed_using_style_main_only(self):
        """
        Test getting content back for a feed using style set to main_only
        """
        self.populate_db_with_documents(3)
        for i in range(3):
            docid = 'julia{0:03d}'.format(i)
            doc = self.db[docid]
            doc.delete()
            with Document(self.db, docid) as doc:
                doc['name'] = 'Jules'
                doc['age'] = i
        feed = Feed(self.db, style='main_only')
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            self.assertEqual(len(change['changes']), 1)
            changes.append(change)
        expected = set(['julia000', 'julia001', 'julia002'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('9'))

    def test_get_feed_using_style_all_docs(self):
        """
        Test getting content back for a feed using style set to "all_docs"
        """
        self.populate_db_with_documents(3)
        for i in range(3):
            docid = 'julia{0:03d}'.format(i)
            doc = self.db[docid]
            doc.delete()
            with Document(self.db, docid) as doc:
                doc['name'] = 'Jules'
                doc['age'] = i
        feed = Feed(self.db, style='all_docs')
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            if not self.cloudant_test:
                self.assertEqual(len(change['changes']), 2)
            changes.append(change)
        expected = set(['julia000', 'julia001', 'julia002'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('9'))

    def test_get_feed_using_since(self):
        """
        Test getting content back for a feed using the since option
        """
        self.populate_db_with_documents(3)
        feed = Feed(self.db)
        changes = [change for change in feed]
        last_seq = feed.last_seq
        self.populate_db_with_documents(3, off_set=3)
        feed = Feed(self.db, since=last_seq)
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
        expected = set(['julia003', 'julia004', 'julia005'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('6'))

    def test_get_feed_using_since_now(self):
        """
        Test getting content back for a feed using since set to "now"
        """
        self.populate_db_with_documents(3)
        feed = Feed(self.db, feed='continuous', heartbeat=1000, since='now')
        changes = list()
        first_pass = True
        beats = 0
        for change in feed:
            if first_pass and not change:
                self.populate_db_with_documents(3, off_set=3)
                first_pass = False
                continue
            elif change:
                self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
                changes.append(change)
                beats = 0
            else:
                beats += 1
            if beats == 15 or len(changes) == 3:
                feed.stop()
        expected = set(['julia003', 'julia004', 'julia005'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)

    def test_get_feed_using_timeout(self):
        """
        Test getting content back for a feed using timeout
        """
        self.populate_db_with_documents()
        feed = Feed(self.db, feed='continuous', timeout=100)
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
        expected = set(['julia{0:03d}'.format(i) for i in range(100)])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('100'))
        # Compare continuous with normal
        normal = Feed(self.db)
        self.assertSetEqual(
            set([x['id'] for x in changes]), set([n['id'] for n in normal]))

    def test_get_feed_using_limit(self):
        """
        Test getting content back for a feed using limit
        """
        self.populate_db_with_documents()
        feed = Feed(self.db, limit=3)
        seq_list = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            seq_list.append(change['seq'])
        self.assertEqual(len(seq_list), 3)
        self.assertTrue(str(seq_list[0]).startswith('1'))
        self.assertTrue(str(seq_list[1]).startswith('2'))
        self.assertTrue(str(seq_list[2]).startswith('3'))
        self.assertEqual(feed.last_seq, seq_list[2])

    def test_get_feed_using_filter(self):
        """
        Test getting content back for a feed using filter
        """
        self.populate_db_with_documents(6)
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc['filters'] = {
            'even_docs': 'function(doc, req){if (doc.age % 2 != 0){return false;} return true;}'
        }
        ddoc.create()
        feed = Feed(self.db, filter='ddoc001/even_docs')
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
        expected = set(['julia000', 'julia002', 'julia004'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('7'))

    def test_get_feed_using_conflicts_true(self):
        """
        Test getting content back for a feed using conflicts set to True.  No
        conflicts were generated but this test ensures that the translation
        process for the conflicts option is working.
        """
        self.populate_db_with_documents(3)
        feed = Feed(self.db, include_docs=True, conflicts=True)
        changes = list()
        for change in feed:
            self.assertSetEqual(
                set(change.keys()), set(['seq', 'changes', 'id', 'doc']))
            changes.append(change)
        expected = set(['julia000', 'julia001', 'julia002'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('3'))

    def test_get_feed_using_conflicts_false(self):
        """
        Test getting content back for a feed using conflicts set to False
        """
        self.populate_db_with_documents(3)
        feed = Feed(self.db, include_docs=True, conflicts=False)
        changes = list()
        for change in feed:
            self.assertSetEqual(
                set(change.keys()), set(['seq', 'changes', 'id', 'doc']))
            changes.append(change)
        expected = set(['julia000', 'julia001', 'julia002'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('3'))

    @unittest.skipIf(os.environ.get('RUN_CLOUDANT_TESTS') is not None,
        'Skipping since _doc_ids filter is not supported on all Cloudant clusters')
    def test_get_feed_using_doc_ids(self):
        """
        Test getting content back for a feed using doc_ids
        """
        self.populate_db_with_documents()
        feed = Feed(self.db, filter='_doc_ids',
            doc_ids=['julia000', 'julia010', 'julia020'])
        changes = list()
        for change in feed:
            self.assertSetEqual(set(change.keys()), set(['seq', 'changes', 'id']))
            changes.append(change)
        expected = set(['julia000', 'julia010', 'julia020'])
        self.assertSetEqual(set([x['id'] for x in changes]), expected)
        self.assertTrue(str(feed.last_seq).startswith('100'))

    def test_invalid_argument(self):
        """
        Test that an invalid argument is caught and an exception is raised
        """
        feed = Feed(self.db, foo='bar')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(str(cm.exception), 'Invalid argument foo')

    def test_invalid_argument_type(self):
        """
        Test that an invalid argument type is caught and an exception is raised
        """
        feed = Feed(self.db, conflicts=0)
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertTrue(
            str(cm.exception).startswith('Argument conflicts not instance of expected type:')
        )

    def test_invalid_non_positive_integer_argument(self):
        """
        Test that an invalid integer argument type is caught and an exception is
        raised
        """
        feed = Feed(self.db, limit=-1)
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(
            str(cm.exception), 'Argument limit must be > 0.  Found: -1')

    def test_invalid_feed_value(self):
        """
        Test that an invalid feed argument value is caught and an exception is
        raised
        """
        feed = Feed(self.db, feed='foo')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertTrue(str(cm.exception).startswith(
            'Invalid value (foo) for feed option.'))

    def test_invalid_style_value(self):
        """
        Test that an invalid feed argument value is caught and an exception is
        raised
        """
        feed = Feed(self.db, style='foo')
        with self.assertRaises(CloudantArgumentError) as cm:
            invalid_feed = [x for x in feed]
        self.assertEqual(
            str(cm.exception), 
            'Invalid value (foo) for style option.  Must be main_only, or all_docs.')

if __name__ == '__main__':
    unittest.main()
