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
Unit tests for Python to CouchDB translation of query parameters.
"""
import unittest

from cloudant.error import CloudantArgumentError
from cloudant._common_util import python_to_couch
from tests.unit._test_util import LONG_NUMBER


class PythonToCouchTests(unittest.TestCase):
    """
    Test cases for validating python_to_couch translation functionality
    """

    def test_valid_descending(self):
        """
        Test descending translation is successful.
        """
        self.assertEqual(
            python_to_couch({'descending': True}),
            {'descending': 'true'}
        )
        self.assertEqual(
            python_to_couch({'descending': False}),
            {'descending': 'false'}
        )

    def test_valid_endkey(self):
        """
        Test endkey translation is successful.
        """
        self.assertEqual(python_to_couch({'endkey': 10}), {'endkey': '10'})
        # Test with long type
        self.assertEqual(python_to_couch({'endkey': LONG_NUMBER}), {'endkey': str(LONG_NUMBER)})
        self.assertEqual(
            python_to_couch({'endkey': 'foo'}),
            {'endkey': '"foo"'}
        )
        self.assertEqual(
            python_to_couch({'endkey': ['foo', 10]}),
            {'endkey': '["foo", 10]'}
        )

        self.assertEqual(
            python_to_couch({'endkey': True}),
            {'endkey': 'true'}
        )

    def test_valid_endkey_docid(self):
        """
        Test endkey_docid translation is successful.
        """
        self.assertEqual(
            python_to_couch({'endkey_docid': 'foo'}),
            {'endkey_docid': 'foo'}
        )

    def test_valid_group(self):
        """
        Test group translation is successful.
        """
        self.assertEqual(python_to_couch({'group': True}), {'group': 'true'})
        self.assertEqual(python_to_couch({'group': False}), {'group': 'false'})

    def test_valid_group_level(self):
        """
        Test group_level translation is successful.
        """
        self.assertEqual(
            python_to_couch({'group_level': 100}),
            {'group_level': 100}
        )
        # Test with long type
        self.assertEqual(
            python_to_couch({'group_level': LONG_NUMBER}),
            {'group_level': LONG_NUMBER}
        )
        self.assertEqual(
            python_to_couch({'group_level': None}),
            {'group_level': None}
        )

    def test_valid_include_docs(self):
        """
        Test include_docs translation is successful.
        """
        self.assertEqual(
            python_to_couch({'include_docs': True}),
            {'include_docs': 'true'}
        )
        self.assertEqual(
            python_to_couch({'include_docs': False}),
            {'include_docs': 'false'}
        )

    def test_valid_inclusive_end(self):
        """
        Test inclusive_end translation is successful.
        """
        self.assertEqual(
            python_to_couch({'inclusive_end': True}),
            {'inclusive_end': 'true'}
        )
        self.assertEqual(
            python_to_couch({'inclusive_end': False}),
            {'inclusive_end': 'false'}
        )

    def test_valid_key(self):
        """
        Test key translation is successful.
        """
        self.assertEqual(python_to_couch({'key': 10}), {'key': '10'})
        # Test with long type
        self.assertEqual(python_to_couch({'key': LONG_NUMBER}), {'key': str(LONG_NUMBER)})
        self.assertEqual(python_to_couch({'key': 'foo'}), {'key': '"foo"'})
        self.assertEqual(
            python_to_couch({'key': ['foo', 10]}),
            {'key': '["foo", 10]'}
        )
        self.assertEqual(
            python_to_couch({'key': True}),
            {'key': 'true'}
        )

    def test_valid_keys(self):
        """
        Test keys translation is successful.
        """
        self.assertEqual(
            python_to_couch({'keys': [100, 200]}),
            {'keys': [100, 200]}
        )
        # Test with long type
        LONG_NUM_KEY = 92233720368547758071
        self.assertEqual(
            python_to_couch({'keys': [LONG_NUMBER, LONG_NUM_KEY]}),
            {'keys': [LONG_NUMBER, LONG_NUM_KEY]}
        )
        self.assertEqual(
            python_to_couch({'keys': ['foo', 'bar']}),
            {'keys': ['foo', 'bar']}
        )
        self.assertEqual(
            python_to_couch({'keys': [['foo', 100], ['bar', 200]]}),
            {'keys': [['foo', 100], ['bar', 200]]}
        )

    def test_valid_limit(self):
        """
        Test limit translation is successful.
        """
        self.assertEqual(python_to_couch({'limit': 100}), {'limit': 100})
        # Test with long type
        self.assertEqual(python_to_couch({'limit': LONG_NUMBER}), {'limit': LONG_NUMBER})
        self.assertEqual(python_to_couch({'limit': None}), {'limit': None})

    def test_valid_reduce(self):
        """
        Test reduce translation is successful.
        """
        self.assertEqual(python_to_couch({'reduce': True}), {'reduce': 'true'})
        self.assertEqual(
            python_to_couch({'reduce': False}),
            {'reduce': 'false'}
        )

    def test_valid_skip(self):
        """
        Test skip translation is successful.
        """
        self.assertEqual(python_to_couch({'skip': 100}), {'skip': 100})
        # Test with long type
        self.assertEqual(python_to_couch({'skip': LONG_NUMBER}), {'skip': LONG_NUMBER})
        self.assertEqual(python_to_couch({'skip': None}), {'skip': None})

    def test_valid_stale(self):
        """
        Test stale translation is successful.
        """
        self.assertEqual(python_to_couch({'stale': 'ok'}), {'stale': 'ok'})
        self.assertEqual(
            python_to_couch({'stale': 'update_after'}),
            {'stale': 'update_after'}
        )

    def test_valid_startkey(self):
        """
        Test startkey translation is successful.
        """
        self.assertEqual(python_to_couch({'startkey': 10}), {'startkey': '10'})
        # Test with long type
        self.assertEqual(python_to_couch({'startkey': LONG_NUMBER}), {'startkey': str(LONG_NUMBER)})
        self.assertEqual(
            python_to_couch({'startkey': 'foo'}),
            {'startkey': '"foo"'}
        )
        self.assertEqual(
            python_to_couch({'startkey': ['foo', 10]}),
            {'startkey': '["foo", 10]'}
        )

        self.assertEqual(
            python_to_couch({'startkey': True}),
            {'startkey': 'true'}
        )

    def test_valid_startkey_docid(self):
        """
        Test startkey_docid translation is successful.
        """
        self.assertEqual(
            python_to_couch({'startkey_docid': 'foo'}),
            {'startkey_docid': 'foo'}
        )

    def test_valid_update(self):
        """
        Test lazy translation is successful.
        """
        self.assertEqual(python_to_couch({'update': 'true'}), {'update': 'true'})
        self.assertEqual(python_to_couch({'update': 'false'}), {'update': 'false'})
        self.assertEqual(python_to_couch({'update': 'lazy'}), {'update': 'lazy'})

    def test_invalid_argument(self):
        """
        Test translation fails when an invalid argument is passed in.
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'foo': 'bar'})
        self.assertEqual(str(cm.exception), 'Invalid argument foo')

    def test_invalid_descending(self):
        """
        Test descending translation fails when a non-bool value is used.
        """
        msg = 'Argument descending not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'descending': 10})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_endkey_docid(self):
        """
        Test endkey_docid translation fails when a non-string value is used.
        """
        msg = 'Argument endkey_docid not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'endkey_docid': 10})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_group(self):
        """
        Test group translation fails when a non-bool value is used.
        """
        msg = 'Argument group not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'group': 10})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_group_level(self):
        """
        Test group_level translation fails when a non-integer value is used.
        """
        msg = 'Argument group_level not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'group_level': True})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_include_docs(self):
        """
        Test include_docs translation fails when a non-bool value is used.
        """
        msg = 'Argument include_docs not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'include_docs': 10})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_inclusive_end(self):
        """
        Test inclusive_end translation fails when a non-bool value is used.
        """
        msg = 'Argument inclusive_end not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'inclusive_end': 10})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_keys_not_list(self):
        """
        Test keys translation fails when a non-list value is used.
        """
        msg = 'Argument keys not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'keys': 'foo'})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_keys_invalid_key(self):
        """
        Test keys translation fails when a key value used in the key list is
        not a valid value.
        """
        msg = 'Key list element not of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'keys': ['foo', True, 'bar']})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_limit(self):
        """
        Test limit translation fails when a non-integer value is used.
        """
        msg = 'Argument limit not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'limit': True})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_reduce(self):
        """
        Test reduce translation fails when a non-bool value is used.
        """
        msg = 'Argument reduce not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'reduce': 10})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_skip(self):
        """
        Test skip translation fails when a non-integer value is used.
        """
        msg = 'Argument skip not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'skip': True})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_stale(self):
        """
        Test stale translation fails when the value is not either
        'ok' or 'update_after' is used.
        """
        msg = 'Argument stale not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'stale': 10})
        self.assertTrue(str(cm.exception).startswith(msg))
        msg = 'Invalid value for stale option foo'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'stale': 'foo'})
        self.assertTrue(str(cm.exception).startswith(msg))

    def test_invalid_startkey_docid(self):
        """
        Test startkey_docid translation fails when a non-string value is used.
        """
        msg = 'Argument startkey_docid not instance of expected type:'
        with self.assertRaises(CloudantArgumentError) as cm:
            python_to_couch({'startkey_docid': 10})
        self.assertTrue(str(cm.exception).startswith(msg))

if __name__ == '__main__':
    unittest.main()
