#!/usr/bin/env python
# Copyright (C) 2019 IBM Corp. All rights reserved.
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
_database_partition_tests_
"""

from cloudant.design_document import DesignDocument
from cloudant.index import Index, SpecialIndex

from nose.plugins.attrib import attr

from .unit_t_db_base import UnitTestDbBase


@attr(db=['cloudant'])
class DatabasePartitionTests(UnitTestDbBase):

    def setUp(self):
        super(DatabasePartitionTests, self).setUp()
        self.db_set_up(partitioned=True)

    def tearDown(self):
        self.db_tear_down()
        super(DatabasePartitionTests, self).tearDown()

    def test_is_partitioned_database(self):
        self.assertTrue(self.db.metadata()['props']['partitioned'])

    def test_create_partitioned_design_document(self):
        ddoc_id = 'empty_ddoc'

        ddoc = DesignDocument(self.db, ddoc_id, partitioned=True)
        ddoc.save()

        r = self.db.r_session.get(ddoc.document_url)
        r.raise_for_status()

        self.assertTrue(r.json()['options']['partitioned'])
        
    def test_create_non_partitioned_design_document(self):
        ddoc_id = 'empty_ddoc'

        ddoc = DesignDocument(self.db, ddoc_id, partitioned=False)
        ddoc.save()

        r = self.db.r_session.get(ddoc.document_url)
        r.raise_for_status()

        self.assertFalse(r.json()['options']['partitioned'])

    def test_partitioned_all_docs(self):
        for partition_key in self.populate_db_with_partitioned_documents(5, 25):
            docs = self.db.partitioned_all_docs(partition_key)
            self.assertEquals(len(docs['rows']), 25)

            for doc in docs['rows']:
                self.assertTrue(doc['id'].startswith(partition_key + ':'))

    def test_partition_metadata(self):
        for partition_key in self.populate_db_with_partitioned_documents(5, 25):
            meta = self.db.partition_metadata(partition_key)
            self.assertEquals(meta['partition'], partition_key)
            self.assertEquals(meta['doc_count'], 25)

    def test_partitioned_search(self):
        ddoc = DesignDocument(self.db, 'partitioned_search', partitioned=True)
        ddoc.add_search_index(
            'search1',
            'function(doc) { index("id", doc._id, {"store": true}); }'
        )
        ddoc.save()

        for partition_key in self.populate_db_with_partitioned_documents(2, 10):
            results = self.db.get_partitioned_search_result(
                partition_key, ddoc['_id'], 'search1', query='*:*')

            i = 0
            for result in results['rows']:
                print(result)
                self.assertTrue(result['id'].startswith(partition_key + ':'))
                i += 1
            self.assertEquals(i, 10)

    def test_get_partitioned_index(self):
        index_name = 'test_partitioned_index'

        self.db.create_query_index(index_name=index_name, fields=['foo'])

        results = self.db.get_query_indexes()
        self.assertEquals(len(results), 2)

        index_all_docs = results[0]
        self.assertEquals(index_all_docs.name, '_all_docs')
        self.assertEquals(type(index_all_docs), SpecialIndex)
        self.assertFalse(index_all_docs.partitioned)

        index_partitioned = results[1]
        self.assertEquals(index_partitioned.name, index_name)
        self.assertEquals(type(index_partitioned), Index)
        self.assertTrue(index_partitioned.partitioned)

    def test_partitioned_query(self):
        self.db.create_query_index(fields=['foo'])

        for partition_key in self.populate_db_with_partitioned_documents(2, 10):
            results = self.db.get_partitioned_query_result(
                partition_key, selector={'foo': {'$eq': 'bar'}})

            i = 0
            for result in results:
                self.assertTrue(result['_id'].startswith(partition_key + ':'))
                i += 1
            self.assertEquals(i, 10)

    def test_partitioned_view(self):
        ddoc = DesignDocument(self.db, 'partitioned_view', partitioned=True)
        ddoc.add_view('view1', 'function(doc) { emit(doc._id, 1); }')
        ddoc.save()

        for partition_key in self.populate_db_with_partitioned_documents(2, 10):
            results = self.db.get_partitioned_view_result(
                partition_key, ddoc['_id'], 'view1')

            i = 0
            for result in results:
                self.assertTrue(
                    result['id'].startswith(partition_key + ':'))
                i += 1
            self.assertEquals(i, 10)
