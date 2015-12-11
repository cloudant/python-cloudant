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
Unit tests for the QueryResult class tested against Cloudant only.

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import os
import posixpath
import requests

from cloudant.query import Query
from cloudant.result import QueryResult
from cloudant.errors import CloudantArgumentError

from unit_t_db_base import UnitTestDbBase

@unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is not None,
    'Skipping Cloudant QueryResult tests'
    )
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

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(QueryResultTests, self).tearDown()

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

    def test_slicing_with_skip_option_fails(self):
        """
        Test __getitem__() fails when "skip" option is provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev'],
            skip=10
        )
        try:
            docs = result[:]
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError, err:
            self.assertEqual(
                str(err),
                'Cannot use skip parameter with QueryResult slicing.'
            )

    def test_slicing_with_limit_option_fails(self):
        """
        Test __getitem__() fails when "limit" option is provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev'],
            limit=10
        )
        try:
            docs = result[:]
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError, err:
            self.assertEqual(
                str(err),
                'Cannot use limit parameter with QueryResult slicing.'
            )

    def test_slicing_with_start(self):
        """
        Test __getitem__() handles when only a start value is provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev']
        )
        self.assertEqual(result[95:], result[95:100])
        self.assertEqual(
            [doc['_id'] for doc in result[95:]],
            ['julia095', 'julia096', 'julia097', 'julia098', 'julia099']
        )

    def test_slicing_with_stop(self):
        """
        Test __getitem__() handles when only a stop value is provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev']
        )
        self.assertEqual(result[:5], result[0:5])
        self.assertEqual(
            [doc['_id'] for doc in result[:5]],
            ['julia000', 'julia001', 'julia002', 'julia003', 'julia004']
        )

    def test_slicing_without_start_stop(self):
        """
        Test __getitem__() handles when neither a start or a stop value is
        provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev']
        )
        self.assertEqual(result[:], result[0:100])
        self.assertEqual(len(result[:]), 100)
        i = 0
        for doc in result[:]:
            self.assertEqual(doc['_id'], 'julia{0:03d}'.format(i))
            i += 1
        self.assertEqual(i, 100)

    def test_slicing_with_start_stop(self):
        """
        Test __getitem__() handles when both a start and stop values are
        provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev']
        )
        self.assertEqual(
            [doc['_id'] for doc in result[5:10]],
            ['julia005', 'julia006', 'julia007', 'julia008', 'julia009']
        )

    def test_slicing_with_same_start_stop(self):
        """
        Test __getitem__() handles when both a start and stop values are same
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev']
        )
        self.assertEqual(result[5:5], [])

    def test_slicing_with_start_gt_stop(self):
        """
        Test __getitem__() fails when start int value > stop int value
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev']
        )
        try:
            docs = result[10:5]
            self.fail('Above statement should raise an Exception')
        except requests.HTTPError, err:
            self.assertEqual(err.response.status_code, 400)

    def test_key_access_is_not_supported(self):
        """
        Test __getitem__() fails when a key value is provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev']
        )
        try:
            docs = result['julia006']
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError, err:
            self.assertEqual(
                str(err),
                'Failed to interpret the argument julia006 as an element slice.'
                '  Only slicing by integer values is supported with '
                'QueryResult.__getitem__.'
            )

    def test_non_integer_value_slicing_is_not_supported(self):
        """
        Test __getitem__() fails when non-integer values for start and stop are
        provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev']
        )
        try:
            docs = result['julia006': 'julia010']
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError, err:
            self.assertEqual(
                str(err),
                'Failed to interpret the argument '
                'slice(\'julia006\', \'julia010\', None) as an element slice.'
                '  Only slicing by integer values is supported with '
                'QueryResult.__getitem__.'
            )

    def test_iteration_with_skip_option_fails(self):
        """
        Test __iter__() fails when "skip" option is provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev'],
            skip=10
        )
        try:
            for doc in result:
                self.fail('Above statement should raise an Exception')
        except CloudantArgumentError, err:
            self.assertEqual(
                str(err),
                'Cannot use skip for iteration'
            )

    def test_iteration_with_limit_option_fails(self):
        """
        Test __iter__() fails when "limit" option is provided
        """
        self.populate_db_with_documents(100)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev'],
            limit=10
        )
        try:
            for doc in result:
                self.fail('Above statement should raise an Exception')
        except CloudantArgumentError, err:
            self.assertEqual(
                str(err),
                'Cannot use limit for iteration'
            )

    def test_iteration_invalid_page_size(self):
        """
        Test __iter__() fails as expected when page_size is set to 0 or less
        """
        self.populate_db_with_documents(5)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev'],
            page_size=0
        )
        try:
            for doc in result:
                self.fail('Above statement should raise an Exception')
        except CloudantArgumentError, err:
            self.assertEqual(str(err), 'Invalid page_size: 0')

    def test_iteration_result_eq_page_size(self):
        """
        Test __iter__() works as expected when the result size is equal to the
        page_size
        """
        self.populate_db_with_documents(5)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev'],
            page_size=5
        )
        self.assertEqual(
            [doc['_id'] for doc in result],
            ['julia000', 'julia001', 'julia002', 'julia003', 'julia004']
        )

    def test_iteration_result_gt_page_size(self):
        """
        Test __iter__() works as expected when the result size is more than the
        page_size
        """
        self.populate_db_with_documents(5)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev'],
            page_size=3
        )
        self.assertEqual(
            [doc['_id'] for doc in result],
            ['julia000', 'julia001', 'julia002', 'julia003', 'julia004']
        )

    def test_iteration_result_lt_page_size(self):
        """
        Test __iter__() works as expected when the result size is less than the
        page_size
        """
        self.populate_db_with_documents(5)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$gt': 0}},
            fields=['_id', '_rev'],
            page_size=100
        )
        self.assertEqual(
            [doc['_id'] for doc in result],
            ['julia000', 'julia001', 'julia002', 'julia003', 'julia004']
        )

    def test_iteration_no_results(self):
        """
        Test __iter__() returns empty result set when no results are found
        """
        self.populate_db_with_documents(5)
        result = QueryResult(
            Query(self.db),
            selector={'_id': {'$lt': 0}},
            fields=['_id', '_rev'],
            page_size=100
        )
        self.assertEqual([doc['_id'] for doc in result], [])

if __name__ == '__main__':
    unittest.main()
