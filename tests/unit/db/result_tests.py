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
result module - Unit tests for Result class
"""
import unittest
import os
from requests.exceptions import HTTPError

from cloudant.errors import ResultException
from cloudant.result import Result, ResultByKey

from .unit_t_db_base import UnitTestDbBase

class ResultExceptionTests(unittest.TestCase):
    """
    Ensure ResultException functions as expected.
    """

    def test_raise_without_code(self):
        """
        Ensure that a default exception/code is used if none is provided.
        """
        with self.assertRaises(ResultException) as cm:
            raise ResultException()
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_using_invalid_code(self):
        """
        Ensure that a default exception/code is used if invalid code is provided.
        """
        with self.assertRaises(ResultException) as cm:
            raise ResultException('foo')
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_without_args(self):
        """
        Ensure that a default exception/code is used if the message requested
        by the code provided requires an argument list and none is provided.
        """
        with self.assertRaises(ResultException) as cm:
            raise ResultException(101)
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_without_insufficient_args(self):
        """
        Ensure that a default exception/code is used if the message requested
        by the code provided requires an argument list but the one provided
        does not contain the correct amount of arguments.
        """
        with self.assertRaises(ResultException) as cm:
            raise ResultException(102, 'foo')
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_with_proper_code_and_args(self):
        """
        Ensure that the requested exception is raised.
        """
        with self.assertRaises(ResultException) as cm:
            raise ResultException(102, 'foo', 'bar')
        self.assertEqual(cm.exception.status_code, 102)

class ResultTests(UnitTestDbBase):
    """
    Result unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(ResultTests, self).setUp()
        self.db_set_up()
        self.populate_db_with_documents()
        self.create_views()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(ResultTests, self).tearDown()

    def test_constructor(self):
        """
        Test instantiating a Result
        """
        result = Result(
            self.ddoc.get_view('view001'),
            startkey='1',
            endkey='9',
            page_size=1000
        )
        self.assertIsInstance(result, Result)
        self.assertDictEqual(result.options, {'startkey': '1', 'endkey': '9'})

    def test_get_item_by_index(self):
        """
        Test retrieving a result using a value that refers to an index of the
        result.
        """
        result = Result(self.view001)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1}]
        self.assertEqual(result[0], expected)
        expected = [{'key': 'julia010', 'id': 'julia010', 'value': 1}]
        self.assertEqual(result[10], expected)
        expected = [{'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[99], expected)
        self.assertEqual(result[100], [])
        self.assertEqual(result[110], [])

    def test_get_item_by_index_using_skip_limit(self):
        """
        Test retrieving a result using a value that refers to an index of the
        result when the result uses skip and limit.
        """
        result = Result(self.view001, skip=10, limit=10)
        expected = [{'key': 'julia010', 'id': 'julia010', 'value': 1}]
        self.assertEqual(result[0], expected)
        expected = [{'key': 'julia015', 'id': 'julia015', 'value': 1}]
        self.assertEqual(result[5], expected)
        expected = [{'key': 'julia019', 'id': 'julia019', 'value': 1}]
        self.assertEqual(result[9], expected)
        self.assertEqual(result[10], [])
        self.assertEqual(result[20], [])

    def test_get_item_by_index_using_limit(self):
        """
        Test retrieving a result using a value that refers to an index of the
        result when the result uses limit.
        """
        result = Result(self.view001, limit=10)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1}]
        self.assertEqual(result[0], expected)
        expected = [{'key': 'julia005', 'id': 'julia005', 'value': 1}]
        self.assertEqual(result[5], expected)
        expected = [{'key': 'julia009', 'id': 'julia009', 'value': 1}]
        self.assertEqual(result[9], expected)
        self.assertEqual(result[10], [])
        self.assertEqual(result[20], [])

    def test_get_item_by_index_using_skip(self):
        """
        Test retrieving a result using a value that refers to an index of the
        result when the result uses limit.
        """
        result = Result(self.view001, skip=10)
        expected = [{'key': 'julia010', 'id': 'julia010', 'value': 1}]
        self.assertEqual(result[0], expected)
        expected = [{'key': 'julia015', 'id': 'julia015', 'value': 1}]
        self.assertEqual(result[5], expected)
        expected = [{'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[89], expected)
        self.assertEqual(result[90], [])
        self.assertEqual(result[100], [])

    def test_get_item_by_negative_index(self):
        """
        Test retrieving a result raises an exception when using a negative index.
        """
        result = Result(self.view001)
        with self.assertRaises(ResultException) as cm:
            invalid_result = result[-1]
        self.assertEqual(cm.exception.status_code, 101)

    def test_get_item_by_key_using_invalid_options(self):
        """
        Since the __getitem__ method uses the 'key' parameter to retrieve the
        specified data using a Result, any Result that uses any of 'key',
        'keys', 'startkey' or 'endkey' as arguments would yield unexpected
        results.  For this reason a check was added to ensure that these options
        are not used in this case.  This test verifies that check.
        """
        options = ('key', 'keys', 'startkey', 'endkey')
        for option in options:
            result = Result(self.view001, **{option: 'julia010'})
            with self.assertRaises(ResultException) as cm:
                invalid_result = result['julia000']
            self.assertEqual(cm.exception.status_code, 102)

    def test_get_item_by_key(self):
        """
        Test retrieving a result using value that refers to a key of the
        result.
        """
        result = Result(self.view001)
        expected = [{'key': 'julia010', 'id': 'julia010', 'value': 1}]
        self.assertEqual(result['julia010'], expected)
        self.assertEqual(result[ResultByKey('julia010')], expected)

    def test_get_item_by_missing_key(self):
        """
        Test retrieving a result using value that refers to a key that does not
        exist in the result.
        """
        result = Result(self.view001)
        self.assertEqual(result['ruby010'], [])
        self.assertEqual(result[ResultByKey('ruby010')], [])

    def test_get_item_by_complex_key(self):
        """
        Test retrieving a result using value that refers to a complex key of the
        result.
        """
        result = Result(self.view005)
        expected = [{'key': ['julia', 10], 'id': 'julia010', 'value': 1}]
        self.assertEqual(result[['julia', 10]], expected)
        self.assertEqual(result[ResultByKey(['julia', 10])], expected)

    def test_get_item_by_integer_key(self):
        """
        Test retrieving a result using an integer value that refers to a key of
        the result.
        """
        result = Result(self.view003)
        expected = [{'key': 10, 'id': 'julia020', 'value': 1},
                    {'key': 10, 'id': 'julia021', 'value': 1}]
        self.assertEqual(result[ResultByKey(10)], expected)

    def test_get_item_by_missing_integer_key(self):
        """
        Test retrieving a result using an integer value that refers to a key
        that does not exist in the result.
        """
        result = Result(self.view003)
        self.assertEqual(result[ResultByKey(99)], [])

    def test_get_item_slice_no_start_no_stop(self):
        """
        Test that by not providing a start and a stop slice value, the entire
        result is returned.
        """
        result = Result(self.view001, limit=3)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1},
                    {'key': 'julia001', 'id': 'julia001', 'value': 1},
                    {'key': 'julia002', 'id': 'julia002', 'value': 1}]
        self.assertEqual(result[:], expected)

    def test_get_item_invalid_index_slice(self):
        """
        Test that when invalid start and stop values are provided in a slice
        an exception is raised.
        """
        result = Result(self.view001)
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
            invalid_result = result[2: 2]
        self.assertEqual(cm.exception.status_code, 101)

        with self.assertRaises(ResultException) as cm:
            invalid_result = result[5: 2]
        self.assertEqual(cm.exception.status_code, 101)

    def test_get_item_index_slice_using_start_stop(self):
        """
        Test getting an index slice by using start and stop slice values.
        """
        result = Result(self.view001)
        expected = [{'key': 'julia098', 'id': 'julia098', 'value': 1},
                    {'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[98:100], expected)
        self.assertEqual(result[98:102], expected)
        self.assertEqual(result[100:102], [])

        result = Result(self.view001, limit=20)
        expected = [{'key': 'julia018', 'id': 'julia018', 'value': 1},
                    {'key': 'julia019', 'id': 'julia019', 'value': 1}]
        self.assertEqual(result[18:20], expected)
        self.assertEqual(result[18:22], expected)
        self.assertEqual(result[20:22], [])

        result = Result(self.view001, skip=98)
        expected = [{'key': 'julia098', 'id': 'julia098', 'value': 1},
                    {'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[0:2], expected)
        self.assertEqual(result[0:4], expected)
        self.assertEqual(result[2:4], [])

        result = Result(self.view001, limit=20, skip=20)
        expected = [{'key': 'julia038', 'id': 'julia038', 'value': 1},
                    {'key': 'julia039', 'id': 'julia039', 'value': 1}]
        self.assertEqual(result[18:20], expected)
        self.assertEqual(result[18:22], expected)
        self.assertEqual(result[20:22], [])

    def test_get_item_index_slice_using_start_only(self):
        """
        Test getting an index slice by using start slice value only.
        """
        result = Result(self.view001)
        expected = [{'key': 'julia098', 'id': 'julia098', 'value': 1},
                    {'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[98:], expected)
        self.assertEqual(result[100:], [])

        result = Result(self.view001, limit=20)
        expected = [{'key': 'julia018', 'id': 'julia018', 'value': 1},
                    {'key': 'julia019', 'id': 'julia019', 'value': 1}]
        self.assertEqual(result[18:], expected)
        self.assertEqual(result[20:], [])

        result = Result(self.view001, skip=98)
        expected = [{'key': 'julia098', 'id': 'julia098', 'value': 1},
                    {'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[0:], expected)
        self.assertEqual(result[2:], [])

        result = Result(self.view001, limit=20, skip=20)
        expected = [{'key': 'julia038', 'id': 'julia038', 'value': 1},
                    {'key': 'julia039', 'id': 'julia039', 'value': 1}]
        self.assertEqual(result[18:], expected)
        self.assertEqual(result[20:], [])

    def test_get_item_index_slice_using_stop_only(self):
        """
        Test getting an index slice by using stop slice value only.
        """
        result = Result(self.view001)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1},
                    {'key': 'julia001', 'id': 'julia001', 'value': 1}]
        self.assertEqual(result[:2], expected)
        expected = [{'key': 'julia{0:03d}'.format(x), 
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(100)]
        self.assertEqual(result[:102], expected)

        result = Result(self.view001, limit=20)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1},
                    {'key': 'julia001', 'id': 'julia001', 'value': 1}]
        self.assertEqual(result[:2], expected)
        expected = [{'key': 'julia{0:03d}'.format(x), 
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(20)]
        self.assertEqual(result[:22], expected)

        result = Result(self.view001, skip=98)
        expected = [{'key': 'julia098', 'id': 'julia098', 'value': 1},
                    {'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[:2], expected)
        self.assertEqual(result[:4], expected)

        result = Result(self.view001, limit=2, skip=20)
        expected = [{'key': 'julia020', 'id': 'julia020', 'value': 1},
                    {'key': 'julia021', 'id': 'julia021', 'value': 1}]
        self.assertEqual(result[:2], expected)
        self.assertEqual(result[:4], expected)

    def test_get_item_key_slice_using_invalid_options(self):
        """
        Test that when "key" and/or "keys" are used in the result an exception
        is raised.
        """
        result = Result(self.view001, key='foo')
        with self.assertRaises(ResultException) as cm:
            invalid_result = result['foo':]
        self.assertEqual(cm.exception.status_code, 102)

        result = Result(self.view001, keys=['foo', 'bar'])
        with self.assertRaises(ResultException) as cm:
            invalid_result = result['foo':]
        self.assertEqual(cm.exception.status_code, 102)

        result = Result(self.view001, startkey='foo')
        with self.assertRaises(ResultException) as cm:
            invalid_result = result['foo':]
        self.assertEqual(cm.exception.status_code, 102)

        result = Result(self.view001, endkey='foo')
        with self.assertRaises(ResultException) as cm:
            invalid_result = result['foo':]
        self.assertEqual(cm.exception.status_code, 102)

    def test_get_item_invalid_key_slice(self):
        """
        Test that when invalid start and stop values are provided in a slice
        an exception is raised.  Specifically this happens when the slice start
        and stop are different types.
        """
        result = Result(self.view001)
        with self.assertRaises(ResultException) as cm:
            invalid_result = result['foo': ['bar', 'baz']]
        self.assertEqual(cm.exception.status_code, 101)

        ten = ResultByKey(10)
        with self.assertRaises(ResultException) as cm:
            invalid_result = result['foo': ten]
        self.assertEqual(cm.exception.status_code, 101)

    def test_get_item_key_slice_using_start_stop(self):
        """
        Test getting a key slice by using start and stop slice values.
        """
        result = Result(self.view001)
        expected = [{'key': 'julia097', 'id': 'julia097', 'value': 1},
                    {'key': 'julia098', 'id': 'julia098', 'value': 1},
                    {'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result['julia097': 'julia099'], expected)
        self.assertEqual(
            result[ResultByKey('julia097'): ResultByKey('julia099')],
            expected
        )
        self.assertEqual(result['julia097': 'ruby'], expected)
        self.assertEqual(
            result['julia098': 'julia098'],
            [{'key': 'julia098', 'id': 'julia098', 'value': 1}]
        )
        self.assertEqual(result['bar': 'foo'], [])

        result = Result(self.view003)
        expected = [{'key': 47, 'id': 'julia094', 'value': 1},
                    {'key': 47, 'id': 'julia095', 'value': 1},
                    {'key': 48, 'id': 'julia096', 'value': 1},
                    {'key': 48, 'id': 'julia097', 'value': 1},
                    {'key': 49, 'id': 'julia098', 'value': 1},
                    {'key': 49, 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[ResultByKey(47): ResultByKey(49)], expected)
        self.assertEqual(result[ResultByKey(47): ResultByKey(52)], expected)
        self.assertEqual(
            result[ResultByKey(48): ResultByKey(48)],
            [{'key': 48, 'id': 'julia096', 'value': 1}, {'key': 48, 'id': 'julia097', 'value': 1}]
        )
        self.assertEqual(result[ResultByKey(52): ResultByKey(54)], [])

        result = Result(self.view005)
        expected = [{'key': ['julia', 97], 'id': 'julia097', 'value': 1},
                    {'key': ['julia', 98], 'id': 'julia098', 'value': 1},
                    {'key': ['julia', 99], 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[['julia', 97]: ['julia', 99]], expected)
        self.assertEqual(
            result[ResultByKey(['julia', 97]): ResultByKey(['julia', 99])],
            expected
        )
        self.assertEqual(result[['julia', 97]: ['ruby', 97]], expected)
        self.assertEqual(
            result[['julia', 98]: ['julia', 98]],
            [{'key': ['julia', 98], 'id': 'julia098', 'value': 1}]
        )
        self.assertEqual(result[['ruby', 'bar']: ['ruby', 'foo']], [])

    def test_get_item_key_slice_start_greater_than_stop(self):
        """
        Test getting a key slice by using start value greater than stop value.
        The behavior when using CouchDB is to return an HTTP 400 Bad Request
        error whereas with Cloudant an empty result collection is returned.
        Unfortunately a 400 response cannot definitively be attributed to a
        startkey value being greater than an endkey value so the decision to
        leave this CouchDB/Cloudant behavior inconsistency as is.  We have an
        "if-else" branch as part of the test to handle the two differing
        behaviors.
        """
        result = Result(self.view001)
        if os.environ.get('RUN_CLOUDANT_TESTS') is None:
            with self.assertRaises(HTTPError) as cm:
                invalid_result = result['foo': 'bar']
            self.assertTrue(
                str(cm.exception).startswith('400 Client Error: Bad Request'))
        else:
            self.assertEqual(result['foo': 'bar'], [])

    def test_get_item_key_slice_using_start_only(self):
        """
        Test getting a key slice by using the start slice value only.
        """
        result = Result(self.view001)
        expected = [{'key': 'julia097', 'id': 'julia097', 'value': 1},
                    {'key': 'julia098', 'id': 'julia098', 'value': 1},
                    {'key': 'julia099', 'id': 'julia099', 'value': 1}]
        self.assertEqual(result['julia097':], expected)
        self.assertEqual(result[ResultByKey('julia097'):], expected)
        self.assertEqual(result['ruby':], [])

        result = Result(self.view003)
        expected = [{'key': 47, 'id': 'julia094', 'value': 1},
                    {'key': 47, 'id': 'julia095', 'value': 1},
                    {'key': 48, 'id': 'julia096', 'value': 1},
                    {'key': 48, 'id': 'julia097', 'value': 1},
                    {'key': 49, 'id': 'julia098', 'value': 1},
                    {'key': 49, 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[ResultByKey(47):], expected)
        self.assertEqual(result[ResultByKey(52):], [])

        result = Result(self.view005)
        expected = [{'key': ['julia', 97], 'id': 'julia097', 'value': 1},
                    {'key': ['julia', 98], 'id': 'julia098', 'value': 1},
                    {'key': ['julia', 99], 'id': 'julia099', 'value': 1}]
        self.assertEqual(result[['julia', 97]:], expected)
        self.assertEqual(result[ResultByKey(['julia', 97]):], expected)
        self.assertEqual(result[ResultByKey(['ruby', 'foo']):], [])

    def test_get_item_key_slice_using_stop_only(self):
        """
        Test getting a key slice by using the stop slice value only.
        """
        result = Result(self.view001)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1},
                    {'key': 'julia001', 'id': 'julia001', 'value': 1},
                    {'key': 'julia002', 'id': 'julia002', 'value': 1}]
        self.assertEqual(result[:'julia002'], expected)
        self.assertEqual(result[:ResultByKey('julia002')], expected)
        self.assertEqual(
            result[:'ruby'],
            [{'key': 'julia{0:03d}'.format(x), 
              'id': 'julia{0:03d}'.format(x),
              'value': 1} for x in range(100)]
        )
        self.assertEqual(result[:'foo'], [])

        result = Result(self.view003)
        expected = [{'key': 0, 'id': 'julia000', 'value': 1},
                    {'key': 0, 'id': 'julia001', 'value': 1},
                    {'key': 1, 'id': 'julia002', 'value': 1},
                    {'key': 1, 'id': 'julia003', 'value': 1},
                    {'key': 2, 'id': 'julia004', 'value': 1},
                    {'key': 2, 'id': 'julia005', 'value': 1}]
        self.assertEqual(result[:ResultByKey(2)], expected)
        self.assertEqual(
            result[:ResultByKey(51)],
            [{'key': x // 2, 
              'id': 'julia{0:03d}'.format(x),
              'value': 1} for x in range(100)]
        )
        self.assertEqual(result[:ResultByKey(-10)], [])

        result = Result(self.view005)
        expected = [{'key': ['julia', 0], 'id': 'julia000', 'value': 1},
                    {'key': ['julia', 1], 'id': 'julia001', 'value': 1},
                    {'key': ['julia', 2], 'id': 'julia002', 'value': 1}]
        self.assertEqual(result[:['julia', 2]], expected)
        self.assertEqual(result[:ResultByKey(['julia', 2])], expected)
        self.assertEqual(
            result[:['julia', 102]],
            [{'key': ['julia', x], 
              'id': 'julia{0:03d}'.format(x),
              'value': 1} for x in range(100)]
        )
        self.assertEqual(result[:ResultByKey(['foo', 'bar'])], [])

    def test_iteration_with_invalid_options(self):
        """
        Test that iteration raises an exception when "skip" and/or "limit" are
        used as options for the result.
        """
        result = Result(self.view001, skip=10)
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 103)

        result = Result(self.view001, limit=10)
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 103)

        result = Result(self.view001, skip=10, limit=10)
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 103)

    def test_iteration_invalid_page_size(self):
        """
        Test that iteration raises an exception when and invalid "page_size" is
        is used as an option for the result.
        """
        result = Result(self.view001, page_size=-1)
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 104)

        result = Result(self.view001, page_size='foo')
        with self.assertRaises(ResultException) as cm:
            invalid_result = [row for row in result]
        self.assertEqual(cm.exception.status_code, 104)

    def test_iteration_using_valid_page_size(self):
        """
        Test that iteration works as expected when "page_size" is provided as
        an option for the result.
        """
        result = Result(self.view001, endkey='julia004', page_size=3)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1},
                    {'key': 'julia001', 'id': 'julia001', 'value': 1},
                    {'key': 'julia002', 'id': 'julia002', 'value': 1},
                    {'key': 'julia003', 'id': 'julia003', 'value': 1},
                    {'key': 'julia004', 'id': 'julia004', 'value': 1}]
        self.assertEqual([x for x in result], expected)
        result = Result(self.view001, endkey='julia004', page_size='3')
        self.assertEqual([x for x in result], expected)

        result = Result(self.view001, endkey='julia002', page_size=3)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1},
                    {'key': 'julia001', 'id': 'julia001', 'value': 1},
                    {'key': 'julia002', 'id': 'julia002', 'value': 1}]
        self.assertEqual([x for x in result], expected)

        result = Result(self.view001, endkey='julia001', page_size=3)
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1},
                    {'key': 'julia001', 'id': 'julia001', 'value': 1}]
        self.assertEqual([x for x in result], expected)

    def test_iteration_using_default_page_size(self):
        """
        Test that iteration works as expected when "page_size" is not provided
        as an option for the result.
        """
        result = Result(self.view001, endkey='julia004')
        expected = [{'key': 'julia000', 'id': 'julia000', 'value': 1},
                    {'key': 'julia001', 'id': 'julia001', 'value': 1},
                    {'key': 'julia002', 'id': 'julia002', 'value': 1},
                    {'key': 'julia003', 'id': 'julia003', 'value': 1},
                    {'key': 'julia004', 'id': 'julia004', 'value': 1}]
        self.assertEqual([x for x in result], expected)

    def test_iteration_no_data(self):
        """
        Test that iteration works as expected when no data matches the result.
        """
        result = Result(self.view001, startkey='ruby')
        self.assertEqual([x for x in result], [])

if __name__ == '__main__':
    unittest.main()
