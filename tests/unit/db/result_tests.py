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
from __future__ import absolute_import

import unittest

from cloudant.design_document import DesignDocument
from cloudant.errors import CloudantArgumentError
from cloudant.result import python_to_couch, Result

from .unit_t_db_base import UnitTestDbBase

class PythonToCouchTests(unittest.TestCase):
    """
    Test cases for validating python_to_couch's options
    """

    # TODO more python_to_couch test cases to be added to completely cover issue #42

    def test_valid_option_group_level(self):
        """
        Test group_level option is valid
        """
        opts = {'group_level': 100}
        translation = python_to_couch(opts)
        self.assertEqual(translation['group_level'], 100)

    def test_invalid_option_group_level(self):
        """
        Test group_level options are invalid
        """
        opts = {'group_level': True}
        self.assertRaises(CloudantArgumentError, python_to_couch, opts)
        opts = {'group_level': '100'}
        self.assertRaises(CloudantArgumentError, python_to_couch, opts)

class ResultTests(UnitTestDbBase):
    """
    Result unit tests
    """

    # TODO more Result test cases to be added to completely cover issue #42

    def setUp(self):
        """
        Set up test attributes
        """
        super(ResultTests, self).setUp()
        self.db_set_up()
        self.ddoc = DesignDocument(self.db, 'ddoc001')
        self.ddoc.add_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}',
            '_count'
        )
        self.ddoc.save()

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

    def test_group_level(self):
        """
        Test group_level option in Result
        """
        self.populate_db_with_documents(10)
        result_set = Result(self.ddoc.get_view('view001'), group_level=1)
        self.assertIsInstance(result_set, Result)
        self.assertDictEqual(result_set.options, {'group_level': 1})
        # Test Result iteration
        i = 0
        for result in result_set:
            self.assertEqual(
                result,
                {'key': 'julia{0:03d}'.format(i), 'value': 1}
            )
            i += 1
        # Test Result key retrieval
        self.assertEqual(
            result_set['julia000'],
            [{'key': 'julia000', 'value': 1}]
        )
        # Test Result key slicing
        self.assertEqual(
            result_set['julia001': 'julia003'],
            [
                {'key': 'julia001', 'value': 1},
                {'key': 'julia002', 'value': 1},
                {'key': 'julia003', 'value': 1}
            ]
        )
        # Test Result element slicing
        self.assertEqual(
            result_set[9:],
            [
                {'key': 'julia009', 'value': 1},
            ]
        )

if __name__ == '__main__':
    unittest.main()
