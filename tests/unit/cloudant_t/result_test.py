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
_result_test_

result module unit tests

"""
import datetime
import unittest

from cloudant.result import python_to_couch, Result, type_or_none
from cloudant.errors import CloudantArgumentError

import mock


class PythonToCouchTests(unittest.TestCase):
    """
    test cases for handling checks of python_to_couch function
    """
    def test_valid_option_types(self):
        """test with valid options"""

        opts = {
            "descending": True,
            "endkey": ['string'],
            "endkey_docid": 'string',
            "group": True,
            "group_level": "string",
            "include_docs": True,
            "inclusive_end": True,
            "key": 12,
            "limit": 12,
            "reduce": True,
            "skip": 12,
            "stale": "ok",
            "startkey": ["string"],
            "startkey_docid": "string"
        }
        result = python_to_couch(opts)
        self.assertEqual(result['include_docs'], 'true')
        self.assertEqual(result['endkey'], '["string"]')
        self.assertEqual(result['skip'], 12)
        self.assertEqual(result['endkey_docid'], '"string"')
        self.assertEqual(result['stale'], '"ok"')

    def test_other_valid_option_combos(self):
        result = python_to_couch({"skip": None})
        self.assertEqual(result['skip'], None)

    def test_invalid_option_raises(self):
        self.assertRaises(CloudantArgumentError, python_to_couch, 
            {"womp": "womp"})
        self.assertRaises(CloudantArgumentError, python_to_couch, 
            {"group": "womp"})
        self.assertRaises(CloudantArgumentError, python_to_couch, 
            {"stale": "womp"})

        # this datetime triggers an argument conversion error
        self.assertRaises(CloudantArgumentError, python_to_couch, 
            {'endkey': [1,2,3, datetime.datetime.utcnow()]})

    def test_type_or_none(self):
        self.assertTrue(type_or_none((int, float), 1))
        self.assertTrue(type_or_none((int, float), 1.0))
        self.assertTrue(type_or_none((int, float), None))
        self.assertTrue(not type_or_none((int, float), "womp"))


class ResultTests(unittest.TestCase):
    """
    tests for Result class
    """
    def test_result_getitem(self):
        ref = mock.Mock()
        ref.return_value = {'rows': [1,2,3]}
        rslt = Result(ref)

        # string key:
        self.assertEqual(rslt["abc"], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(key='abc'))
        self.assertEqual(rslt[["abc", "def"]], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(key=['abc', 'def']))

        # list slice
        self.assertEqual(rslt["abc":"def"], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(startkey='abc', endkey='def'))
        self.assertEqual(rslt["abc":], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(startkey='abc'))
        self.assertEqual(rslt[:"def"], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(endkey='def'))
        self.assertEqual(rslt[:], [1,2,3])
        self.assertEqual(ref.call_args, mock.call())

        # int slice
        self.assertEqual(rslt[1:100], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(skip=1, limit=99))
        self.assertEqual(rslt[1:], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(skip=1))
        self.assertEqual(rslt[:100], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(limit=100))

        self.assertRaises(CloudantArgumentError, rslt.__getitem__, {})

    def test_iter_method(self):
        """test basics of iter method"""
        ref = mock.Mock()
        ref.side_effect = [{'rows': [1,2,3]}, {'rows': []}]
        rslt = Result(ref)
        collection = [x for x in rslt]
        self.assertEqual(collection, [1,2,3])

        run_iter = lambda x: [y for y in x]

        rslt = Result(ref, skip=1000)
        self.assertRaises(CloudantArgumentError, run_iter, rslt)

        rslt = Result(ref, limit=1000)
        self.assertRaises(CloudantArgumentError, run_iter, rslt)

    def test_iter_paging(self):
        """iterate with multiple pages of data"""
        ref = mock.Mock()
        ref.side_effect = [
            {'rows': [x for x in range(100)]},
            {'rows': []}
        ]
        rslt = Result(ref, page_size=10)
        collection = [x for x in rslt]
        self.assertEqual(len(collection), 100)

if __name__ == '__main__':
    unittest.main()
