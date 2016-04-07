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
Unit tests for the Query class tested against Cloudant only.

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import os
import posixpath

from cloudant.query import Query
from cloudant.result import QueryResult
from cloudant.error import CloudantArgumentError

from .unit_t_db_base import UnitTestDbBase

@unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is not None,
    'Skipping Cloudant Query tests'
    )
class QueryTests(UnitTestDbBase):
    """
    Query unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(QueryTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(QueryTests, self).tearDown()

    def test_constructor_with_kwargs(self):
        """
        Test instantiating a Query by passing in query parameters
        """
        query = Query(self.db, foo={'bar': 'baz'})
        self.assertIsInstance(query, Query)
        self.assertIsInstance(query.result, QueryResult)
        self.assertEqual(query, {'foo': {'bar': 'baz'}})

    def test_constructor_without_kwargs(self):
        """
        Test instantiating a Query without parameters
        """
        query = Query(self.db)
        self.assertIsInstance(query, Query)
        self.assertIsInstance(query.result, QueryResult)
        self.assertEqual(query, {})

    def test_retrieve_query_url(self):
        """
        Test constructing the query test url
        """
        query = Query(self.db)
        self.assertEqual(
            query.url,
            posixpath.join(self.db.database_url, '_find')
        )

    def test_callable_with_invalid_argument(self):
        """
        Test Query __call__ by passing in invalid arguments
        """
        query = Query(self.db)
        try:
            query(foo={'bar': 'baz'})
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(str(err), 'Invalid argument: foo')

    def test_callable_with_invalid_value_types(self):
        """
        Test Query __call__ by passing in invalid selector
        """
        test_data = [
            {'selector': 'blah'},  # Should be a dict
            {'limit': 'blah'},     # Should be an int
            {'skip': 'blah'},      # Should be an int
            {'sort': 'blah'},      # Should be a list
            {'fields': 'blah'},    # Should be a list
            {'r': 'blah'},         # Should be an int
            {'bookmark': 1},       # Should be a basestring
            {'use_index': 1}       # Should be a basestring
        ]

        for argument in test_data:
            query = Query(self.db)
            try:
                query(**argument)
                self.fail('Above statement should raise an Exception')
            except CloudantArgumentError as err:
                self.assertTrue(str(err).startswith(
                    'Argument {0} is not an instance of expected type:'.format(
                        list(argument.keys())[0]
                    )
                ))

    def test_callable_without_selector(self):
        """
        Test Query __call__ without providing a selector
        """
        query = Query(self.db)
        try:
            query(fields=['_id', '_rev'])
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(
                str(err),
                'No selector in the query or the selector was empty.  '
                'Add a selector to define the query and retry.'
            )

    def test_callable_with_empty_selector(self):
        """
        Test Query __call__ without providing a selector
        """
        query = Query(self.db)
        try:
            query(selector={}, fields=['_id', '_rev'])
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(
                str(err),
                'No selector in the query or the selector was empty.  '
                'Add a selector to define the query and retry.'
            )

    def test_callable_executes_query(self):
        """
        Test Query __call__ executes a query
        """
        self.populate_db_with_documents(100)
        query = Query(self.db)
        resp = query(
            selector={'_id': {'$lt': 'julia050'}},
            fields=['_id'],
            sort=[{'_id': 'desc'}],
            skip=10,
            limit=3,
            r=1
        )
        self.assertEqual(
            resp['docs'],
            [{'_id': 'julia039'}, {'_id': 'julia038'}, {'_id': 'julia037'}]
        )

    def test_custom_result_context_manager(self):
        """
        Test that custom_result yields a context manager and returns expected
        content
        """
        self.populate_db_with_documents(100)
        query = Query(
            self.db,
            selector={'_id': {'$lt': 'julia050'}},
            fields=['_id'],
            r=1
        )
        with query.custom_result(sort=[{'_id': 'desc'}]) as rslt:
            self.assertEqual(
                rslt[10:13],
                [{'_id': 'julia039'}, {'_id': 'julia038'}, {'_id': 'julia037'}]
            )

if __name__ == '__main__':
    unittest.main()
