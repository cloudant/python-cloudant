#!/usr/bin/env python
# Copyright (C) 2015, 2018 IBM Corp. All rights reserved.
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
Unit tests for the QueryResult class tested against Cloudant only.

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import os

from cloudant.query import Query
from cloudant.result import QueryResult
from cloudant.error import ResultException
from nose.plugins.attrib import attr

from .unit_t_db_base import UnitTestDbBase

@attr(db=['cloudant','couch'])
@attr(couchapi=2)
class QueryResultTests(UnitTestDbBase):
    """
    QueryResult unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(QueryResultTests, self).setUp()
        self.db_set_up()
        self.populate_db_with_documents()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(QueryResultTests, self).tearDown()

    def create_result(self, selector={'_id': {'$gt': 0}},
        fields=['_id', 'name', 'age'], **kwargs):
        if kwargs.get('q_parms', None):
            query = Query(self.db, **kwargs['q_parms'])
        else:
            query = Query(self.db)

        if kwargs.get('qr_parms', None):
            return QueryResult(query, selector=selector, fields=fields, **kwargs['qr_parms'])
        else:
            return QueryResult(query, selector=selector, fields=fields)

    def test_constructor_with_options(self):
        """
        Test instantiating a QueryResult by passing in query parameters
        """
        query = Query(self.db)
        result = QueryResult(query, foo='bar', page_size=10)
        self.assertIsInstance(result, QueryResult)
        self.assertEqual(result.options, {'foo': 'bar'})
        self.assertEqual(result._ref, query)
        self.assertEqual(result._page_size, 10)

    def test_constructor_without_options(self):
        """
        Test instantiating a Query without parameters
        """
        query = Query(self.db)
        result = QueryResult(query)
        self.assertIsInstance(result, QueryResult)
        self.assertEqual(result.options, {})
        self.assertEqual(result._ref, query)
        self.assertEqual(result._page_size, 100)

    def test_constructor_with_query_skip_limit(self):
        """
        Test instantiating a QueryResult when query callable already has
        skip and/or limit
        """
        query = Query(self.db, skip=10, limit=10)
        result = QueryResult(query)
        self.assertIsInstance(result, QueryResult)
        self.assertDictEqual(result.options, {'skip': 10, 'limit': 10})
        self.assertEqual(result._ref, query)

    def test_constructor_with_query_skip_limit_options_skip_limit(self):
        """
        Ensure that options skip and/or limit override the values in the query
        callable if present when constructing a QueryResult
        """
        query = Query(self.db, skip=10, limit=10)
        result = QueryResult(query, skip=100, limit=100)
        self.assertIsInstance(result, QueryResult)
        self.assertDictEqual(result.options, {'skip': 100, 'limit': 100})
        self.assertEqual(result._ref, query)

    def test_key_value_access_is_not_supported(self):
        """
        Test __getitem__() fails when a key value is provided
        """
        result = self.create_result()
        with self.assertRaises(ResultException) as cm:
            invalid_result = result['foo']
        self.assertEqual(cm.exception.status_code, 101)

    def test_key_value_slicing_is_not_supported(self):
        """
        Test __getitem__() fails when non-integer values for start and stop are
        provided
        """
        result = self.create_result()
        with self.assertRaises(ResultException) as cm:
            invalid_result = result['bar': 'foo']
        self.assertEqual(cm.exception.status_code, 101)

    def test_get_item_by_index(self):
        """
        Test retrieving a result using a value that refers to an index of the
        result.
        """
        result = self.create_result()
        expected = {0: [{'_id': 'julia000', 'name': 'julia', 'age': 0}],
                    10: [{'_id': 'julia010', 'name': 'julia', 'age': 10}],
                    99: [{'_id': 'julia099', 'name': 'julia', 'age': 99}],
                    100: [], 110: []}

        for key in expected:
            self.assertEqual(result[key], expected[key])

    def test_get_item_by_index_using_skip_limit(self):
        """
        Test retrieving a result using a value that refers to an index of the
        result when the result uses skip and limit.  QueryResult skip/limit
        parameters take precedence over Query skip/limit parameters.
        """
        results = [self.create_result(q_parms={'skip': 10, 'limit': 10}),
            self.create_result(qr_parms={'skip': 10, 'limit': 10}),
            self.create_result(q_parms={'skip': 100, 'limit': 100},
                qr_parms={'skip': 10, 'limit': 10})]

        expected = {0: [{'_id': 'julia010', 'name': 'julia', 'age': 10}],
                    5: [{'_id': 'julia015', 'name': 'julia', 'age': 15}],
                    9: [{'_id': 'julia019', 'name': 'julia', 'age': 19}],
                    10: [], 20: []}

        for key in expected:
            for result in results:
                self.assertEqual(result[key], expected[key])

    def test_get_item_by_index_using_limit(self):
        """
        Test retrieving a result using a value that refers to an index of the
        result when the result uses limit.  QueryResult limit parameter takes 
        precedence over Query limit parameter.
        """
        results = [self.create_result(q_parms={'limit': 10}),
            self.create_result(qr_parms={'limit': 10}),
            self.create_result(q_parms={'limit': 100}, qr_parms={'limit': 10})]

        expected = {0: [{'_id': 'julia000', 'name': 'julia', 'age': 0}],
                    5: [{'_id': 'julia005', 'name': 'julia', 'age': 5}],
                    9: [{'_id': 'julia009', 'name': 'julia', 'age': 9}],
                    10: [], 20: []}

        for key in expected:
            for result in results:
                self.assertEqual(result[key], expected[key])

    def test_get_item_by_index_using_skip(self):
        """
        Test retrieving a result using a value that refers to an index of the
        result when the result uses skip.  QueryResult skip parameter takes 
        precedence over Query skip parameter.
        """
        results = [self.create_result(q_parms={'skip': 10}),
            self.create_result(qr_parms={'skip': 10}),
            self.create_result(q_parms={'skip': 100}, qr_parms={'skip': 10})]

        expected = {0: [{'_id': 'julia010', 'name': 'julia', 'age': 10}],
                    5: [{'_id': 'julia015', 'name': 'julia', 'age': 15}],
                    89: [{'_id': 'julia099', 'name': 'julia', 'age': 99}],
                    90: [], 100: []}

        for key in expected:
            for result in results:
                self.assertEqual(result[key], expected[key])

    def test_get_item_by_negative_index(self):
        """
        Test retrieving a result raises an exception when using a negative index.
        """
        result = self.create_result()
        with self.assertRaises(ResultException) as cm:
            invalid_result = result[-1]
        self.assertEqual(cm.exception.status_code, 101)

    def test_get_item_slice_no_start_no_stop(self):
        """
        Test that by not providing a start and a stop slice value, the entire
        result is returned.
        """
        result = self.create_result({'_id': {'$lte': 'julia002'}})
        expected = [{'_id': 'julia000', 'name': 'julia', 'age': 0},
                    {'_id': 'julia001', 'name': 'julia', 'age': 1},
                    {'_id': 'julia002', 'name': 'julia', 'age': 2}]
        self.assertEqual(result[:], expected)

    def test_get_item_invalid_index_slice(self):
        """
        Test that when invalid start and stop values are provided in a slice
        an exception is raised.
        """
        result = self.create_result()
        with self.assertRaises(ResultException) as cm:
            invalid_result = result[-1: 10]
        self.assertEqual(cm.exception.status_code, 101)

        with self.assertRaises(ResultException) as cm:
            invalid_result = result[1: -10]
        self.assertEqual(cm.exception.status_code, 101)

        with self.assertRaises(ResultException) as cm:
            invalid_result = result[-1: -10]
        self.assertEqual(cm.exception.status_code, 101)

        with self.assertRaises(ResultException) as cm:
            invalid_result = result[5: 2]
        self.assertEqual(cm.exception.status_code, 101)

        with self.assertRaises(ResultException) as cm:
            invalid_result = result[5: 5]
        self.assertEqual(cm.exception.status_code, 101)

    def test_get_item_index_slice_using_start_stop(self):
        """
        Test getting an index slice by using start and stop slice values.
        """
        result = self.create_result()
        expected = [{'_id': 'julia098', 'name': 'julia', 'age': 98},
                    {'_id': 'julia099', 'name': 'julia', 'age': 99}]
        self.assertEqual(result[98:100], expected)
        self.assertEqual(result[98:102], expected)
        self.assertEqual(result[100:102], [])

    def test_get_item_index_slice_using_start_stop_limit(self):
        """
        Test getting an index slice by using start and stop slice values when
        the limit parameter is also used.  QueryResult limit parameter takes 
        precedence over Query limit parameter.
        """
        results = [self.create_result(q_parms={'limit': 20}),
            self.create_result(qr_parms={'limit': 20}),
            self.create_result(q_parms={'limit': 100}, qr_parms={'limit': 20})]
        expected = [{'_id': 'julia018', 'name': 'julia', 'age': 18},
                    {'_id': 'julia019', 'name': 'julia', 'age': 19}]
        for result in results:
            self.assertEqual(result[18:20], expected)
            self.assertEqual(result[18:22], expected)
            self.assertEqual(result[20:22], [])

    def test_get_item_index_slice_using_start_stop_skip(self):
        """
        Test getting an index slice by using start and stop slice values when
        the skip parameter is also used.  QueryResult skip parameter takes 
        precedence over Query skip parameter.
        """
        results = [self.create_result(q_parms={'skip': 98}),
            self.create_result(qr_parms={'skip': 98}),
            self.create_result(q_parms={'skip': 100}, qr_parms={'skip': 98})]
        expected = [{'_id': 'julia098', 'name': 'julia', 'age': 98},
                    {'_id': 'julia099', 'name': 'julia', 'age': 99}]
        for result in results:
            self.assertEqual(result[0:2], expected)
            self.assertEqual(result[0:4], expected)
            self.assertEqual(result[2:4], [])

    def test_get_item_index_slice_using_start_stop_limit_skip(self):
        """
        Test getting an index slice by using start and stop slice values when
        the skip and limit parameters are also used.  QueryResult skip/limit
        parameters take precedence over Query skip/limit parameters.
        """
        results = [self.create_result(q_parms={'limit': 20, 'skip': 20}),
            self.create_result(qr_parms={'limit': 20, 'skip': 20}),
            self.create_result(q_parms={'limit': 100, 'skip': 100},
                qr_parms={'limit': 20, 'skip': 20})]
        expected = [{'_id': 'julia038', 'name': 'julia', 'age': 38},
                    {'_id': 'julia039', 'name': 'julia', 'age': 39}]
        for result in results:
            self.assertEqual(result[18:20], expected)
            self.assertEqual(result[18:22], expected)
            self.assertEqual(result[20:22], [])

    def test_get_item_index_slice_using_start_only(self):
        """
        Test getting an index slice by using start slice value only.
        """
        result = self.create_result()
        expected = [{'_id': 'julia098', 'name': 'julia', 'age': 98},
                    {'_id': 'julia099', 'name': 'julia', 'age': 99}]
        self.assertEqual(result[98:], expected)
        self.assertEqual(result[100:], [])

    def test_get_item_index_slice_using_start_only_limit(self):
        """
        Test getting an index slice by using a start slice value when
        the limit parameter is also used.  QueryResult limit parameter takes
        precedence over Query limit parameter.
        """
        results = [self.create_result(q_parms={'limit': 20}),
            self.create_result(qr_parms={'limit': 20}),
            self.create_result(q_parms={'limit': 100}, qr_parms={'limit': 20})]
        expected = [{'_id': 'julia018', 'name': 'julia', 'age': 18},
                    {'_id': 'julia019', 'name': 'julia', 'age': 19}]
        for result in results:
            self.assertEqual(result[18:], expected)
            self.assertEqual(result[20:], [])

    def test_get_item_index_slice_using_start_only_skip(self):
        """
        Test getting an index slice by using a start slice value when
        the skip parameter is also used.  QueryResult skip parameter takes
        precedence over Query skip parameter.
        """
        results = [self.create_result(q_parms={'skip': 98}),
            self.create_result(qr_parms={'skip': 98}),
            self.create_result(q_parms={'skip': 100}, qr_parms={'skip': 98})]
        expected = [{'_id': 'julia098', 'name': 'julia', 'age': 98},
                    {'_id': 'julia099', 'name': 'julia', 'age': 99}]
        for result in results:
            self.assertEqual(result[0:], expected)
            self.assertEqual(result[2:], [])

    def test_get_item_index_slice_using_start_only_limit_skip(self):
        """
        Test getting an index slice by using a start slice value when
        the skip and limit parameters are also used.  QueryResult skip/limit
        parameters take precedence over Query skip/limit parameters.
        """
        results = [self.create_result(q_parms={'limit': 20, 'skip': 20}),
            self.create_result(qr_parms={'limit': 20, 'skip': 20}),
            self.create_result(q_parms={'limit': 100, 'skip': 100},
                qr_parms={'limit': 20, 'skip': 20})]
        expected = [{'_id': 'julia038', 'name': 'julia', 'age': 38},
                    {'_id': 'julia039', 'name': 'julia', 'age': 39}]
        for result in results:
            self.assertEqual(result[18:], expected)
            self.assertEqual(result[20:], [])

    def test_get_item_index_slice_using_stop_only(self):
        """
        Test getting an index slice by using stop slice value only.
        """
        result = self.create_result()
        expected = {2: [{'_id': 'julia000', 'name': 'julia', 'age': 0},
                        {'_id': 'julia001', 'name': 'julia', 'age': 1}],
                    102: [{'_id': 'julia{0:03d}'.format(x), 
                           'name': 'julia',
                           'age': x} for x in range(100)]}
        for key in expected:
            self.assertEqual(result[:key], expected[key])

    def test_get_item_index_slice_using_stop_only_limit(self):
        """
        Test getting an index slice by using a stop slice value only when
        the limit parameter is also used.  QueryResult limit parameter takes
        precedence over Query limit parameter.
        """
        results = [self.create_result(q_parms={'limit': 20}),
            self.create_result(qr_parms={'limit': 20}),
            self.create_result(q_parms={'limit': 100}, qr_parms={'limit': 20})]
        expected = {2: [{'_id': 'julia000', 'name': 'julia', 'age': 0},
                        {'_id': 'julia001', 'name': 'julia', 'age': 1}],
                    22: [{'_id': 'julia{0:03d}'.format(x), 
                           'name': 'julia',
                           'age': x} for x in range(20)]}
        for result in results:
            for key in expected:
                self.assertEqual(result[:key], expected[key])

    def test_get_item_index_slice_using_stop_only_skip(self):
        """
        Test getting an index slice by using a stop slice value only when
        the skip parameter is also used.  QueryResult skip parameter takes
        precedence over Query skip parameter.
        """
        results = [self.create_result(q_parms={'skip': 98}),
            self.create_result(qr_parms={'skip': 98}),
            self.create_result(q_parms={'skip': 100}, qr_parms={'skip': 98})]
        expected = [{'_id': 'julia098', 'name': 'julia', 'age': 98},
                    {'_id': 'julia099', 'name': 'julia', 'age': 99}]
        for result in results:
            self.assertEqual(result[:2], expected)
            self.assertEqual(result[:4], expected)

    def test_get_item_index_slice_using_stop_only_limit_skip(self):
        """
        Test getting an index slice by using a start slice value when
        the skip and limit parameters are also used.  QueryResult skip/limit
        parameters take precedence over Query skip/limit parameters.
        """
        results = [self.create_result(q_parms={'limit':2, 'skip': 20}),
            self.create_result(qr_parms={'limit':2, 'skip': 20}),
            self.create_result(q_parms={'limit':100, 'skip': 100},
                qr_parms={'limit':2, 'skip': 20})]
        expected = [{'_id': 'julia020', 'name': 'julia', 'age': 20},
                    {'_id': 'julia021', 'name': 'julia', 'age': 21}]
        for result in results:
            self.assertEqual(result[:2], expected)
            self.assertEqual(result[:4], expected)

    def test_iteration_with_invalid_options(self):
        """
        Test that iteration raises an exception when "skip" and/or "limit" are
        used as options for the result.
        """
        result = self.create_result(q_parms={'skip': 10})
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 103)

        result = self.create_result(q_parms={'limit': 10})
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 103)

        result = self.create_result(q_parms={'limit': 10, 'skip': 10})
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 103)

    def test_iteration_invalid_page_size(self):
        """
        Test that iteration raises an exception when and invalid "page_size" is
        is used as an option for the result.
        """
        result = self.create_result(qr_parms={'page_size': -1})
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 104)

        result = self.create_result(qr_parms={'page_size': 'foo'})
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 104)

    def test_iteration_using_valid_page_size(self):
        """
        Test that iteration works as expected when "page_size" is provided as
        an option for the result.
        """
        result = self.create_result({'_id': {'$lte': 'julia004'}}, qr_parms={'page_size': 3})
        expected = [{'_id': 'julia000', 'name': 'julia', 'age': 0},
                    {'_id': 'julia001', 'name': 'julia', 'age': 1},
                    {'_id': 'julia002', 'name': 'julia', 'age': 2},
                    {'_id': 'julia003', 'name': 'julia', 'age': 3},
                    {'_id': 'julia004', 'name': 'julia', 'age': 4}]
        self.assertEqual([x for x in result], expected)

        result = self.create_result({'_id': {'$lte': 'julia002'}}, qr_parms={'page_size': 3})
        expected = [{'_id': 'julia000', 'name': 'julia', 'age': 0},
                    {'_id': 'julia001', 'name': 'julia', 'age': 1},
                    {'_id': 'julia002', 'name': 'julia', 'age': 2}]
        self.assertEqual([x for x in result], expected)

        result = self.create_result({'_id': {'$lte': 'julia001'}}, qr_parms={'page_size': 3})
        expected = [{'_id': 'julia000', 'name': 'julia', 'age': 0},
                    {'_id': 'julia001', 'name': 'julia', 'age': 1}]
        self.assertEqual([x for x in result], expected)

    def test_iteration_using_default_page_size(self):
        """
        Test that iteration works as expected when "page_size" is not provided
        as an option for the result.
        """
        result = self.create_result({'_id': {'$lte': 'julia004'}})
        expected = [{'_id': 'julia000', 'name': 'julia', 'age': 0},
                    {'_id': 'julia001', 'name': 'julia', 'age': 1},
                    {'_id': 'julia002', 'name': 'julia', 'age': 2},
                    {'_id': 'julia003', 'name': 'julia', 'age': 3},
                    {'_id': 'julia004', 'name': 'julia', 'age': 4}]
        self.assertEqual([x for x in result], expected)

    def test_iteration_no_data(self):
        """
        Test that iteration works as expected when no data matches the result.
        """
        result = self.create_result({'_id': {'$gt': 'ruby'}})
        self.assertEqual([x for x in result], [])

if __name__ == '__main__':
    unittest.main()
