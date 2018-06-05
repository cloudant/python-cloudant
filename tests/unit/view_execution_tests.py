#!/usr/bin/env python
# Copyright (c) 2016, 2018 IBM Corp. All rights reserved.
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
Unit tests for the execution of view queries using translated parameters.
"""
import unittest

from .unit_t_db_base import UnitTestDbBase

class QueryParmExecutionTests(UnitTestDbBase):
    """
    Test cases for the execution of views queries using translated parameters.
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(QueryParmExecutionTests, self).setUp()
        self.db_set_up()
        self.populate_db_with_documents()
        self.create_views()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(QueryParmExecutionTests, self).tearDown()

    def test_descending_true(self):
        """
        Test view query using descending parameter set to True.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(descending=True)['rows']
        expected = [{'key': 'julia{0:03d}'.format(x), 
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(100)]
        self.assertEqual(actual, list(reversed(expected)))

    def test_descending_false(self):
        """
        Test view query using descending parameter set to False.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(descending=False)['rows']
        expected = [{'key': 'julia{0:03d}'.format(x), 
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(100)]
        self.assertEqual(actual, expected)

    def test_endkey_int(self):
        """
        Test view query using endkey parameter as an integer.

        The view used here will generate rows of data where each key will be an
        integer.  Such as:
        {'key': 0, 'id': 'julia000', 'value': 1},
        {'key': 0, 'id': 'julia001', 'value': 1},
        {'key': 1, 'id': 'julia002', 'value': 1},
        {'key': 1, 'id': 'julia003', 'value': 1},
        ...
        {'key': 5, 'id': 'julia010', 'value': 1},
        {'key': 5, 'id': 'julia011', 'value': 1},
        ...
        """
        actual = self.view003(endkey=4)['rows']
        expected = [{'key': x // 2,
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10)]
        self.assertEqual(len(actual), 10)
        self.assertEqual(len(expected), 10)
        self.assertEqual(actual, expected)

    def test_endkey_str(self):
        """
        Test view query using endkey parameter as a string.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(endkey='julia009')['rows']
        expected = [{'key': 'julia{0:03d}'.format(x),
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10)]
        self.assertEqual(len(actual), 10)
        self.assertEqual(len(expected), 10)
        self.assertEqual(actual, expected)

    def test_endkey_complex(self):
        """
        Test view query using endkey parameter as a complex key.

        The view used here will generate rows of data where each key is a
        complex key.  Such as:
        {'key': ['julia', 0], 'id': 'julia000', 'value': 1},
        {'key': ['julia', 1], 'id': 'julia001', 'value': 1},
        {'key': ['julia', 2], 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view005(endkey=['julia', 9])['rows']
        expected = [{'key': ['julia', x],
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10)]
        self.assertEqual(len(actual), 10)
        self.assertEqual(len(expected), 10)
        self.assertEqual(actual, expected)

    def test_endkey_docid(self):
        """
        Test view query using endkey_docid parameter.

        The view used here will generate rows of data where each key will have
        two ids associated with it.  Such as:
        {'key': 0, 'id': 'julia000', 'value': 1},
        {'key': 0, 'id': 'julia001', 'value': 1},
        {'key': 1, 'id': 'julia002', 'value': 1},
        {'key': 1, 'id': 'julia003', 'value': 1},
        ...
        {'key': 5, 'id': 'julia010', 'value': 1},
        {'key': 5, 'id': 'julia011', 'value': 1},
        ...
        """
        # Ensure that only rows of data up to and including the first document 
        # where the key is 5 are returned.
        actual = self.view003(endkey_docid='julia010', endkey=5)['rows']
        expected = [{'key': x // 2,
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(11)]
        self.assertEqual(len(actual), 11)
        self.assertEqual(len(expected), 11)
        self.assertEqual(actual, expected)

    def test_group_true(self):
        """
        Test view query using group parameter set to True.

        The view used here along with group=True will generate rows of
        data where each key will be grouped into groups of 2.  Such as:
        {'key': 0, 'value': 2},
        {'key': 1, 'value': 2},
        {'key': 2, 'value': 2},
        ...
        {'key': 49, 'value': 2}
        """
        actual = self.view004(group=True)['rows']
        expected = [{'key': x, 'value': 2} for x in range(50)]
        self.assertEqual(len(actual), 50)
        self.assertEqual(len(expected), 50)
        self.assertEqual(actual, expected)

    def test_group_false(self):
        """
        Test view query using group parameter set to False.

        The view used here will generate a row of data containing the number of
        documents matching the view query.  Such as:
        {'key': None, 'value': 100}
        """
        actual = self.view004(group=False)['rows']
        self.assertEqual(actual, [{'key': None, 'value': 100}])

    def test_group_level(self):
        """
        Test view query using group_level parameter.

        The view used here along with group_level=1 will generate rows of data
        that calculate the count for a grouping of the first element in the
        complex key defined by this view.  In this case the output will yield a
        single row of data for the key ['julia'].  Such as:

        {'key': ['julia'], 'value': 100}
        """
        actual = self.view006(group_level=1)['rows']
        expected = [{'key': ['julia'], 'value': 100}]
        self.assertEqual(actual, expected)

    def test_include_docs_true(self):
        """
        Test view query using include_docs set to True and the key parameter.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        data = self.view001(key='julia010', include_docs=True)['rows']
        self.assertEqual(len(data), 1)
        self.assertTrue(
            all(x in ['key', 'id', 'value', 'doc'] for x in data[0].keys())
        )
        self.assertEqual(data[0]['key'], 'julia010')
        self.assertEqual(data[0]['id'], 'julia010')
        self.assertEqual(data[0]['value'], 1)
        self.assertTrue(
            all(x in ['_id', '_rev', 'name', 'age'] for x in data[0]['doc'].keys())
        )
        self.assertEqual(data[0]['doc']['_id'], 'julia010')
        self.assertTrue(data[0]['doc']['_rev'].startswith('1-'))
        self.assertEqual(data[0]['doc']['name'], 'julia')
        self.assertEqual(data[0]['doc']['age'], 10)

    def test_include_docs_false(self):
        """
        Test view query using include_docs set to False and the key parameter.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(key='julia010', include_docs=False)['rows']
        expected = [{'key': 'julia010', 'id': 'julia010', 'value': 1}]
        self.assertEqual(actual, expected)

    def test_inclusive_end_true(self):
        """
        Test view query using inclusive_end set to True and the endkey parameter.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(endkey='julia010', inclusive_end=True)['rows']
        expected = [{'key': 'julia{0:03d}'.format(x),
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(11)]
        self.assertEqual(actual, expected)

    def test_inclusive_end_false(self):
        """
        Test view query using inclusive_end set to False and the endkey parameter.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(endkey='julia010', inclusive_end=False)['rows']
        expected = [{'key': 'julia{0:03d}'.format(x),
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10)]
        self.assertEqual(actual, expected)

    def test_key_int(self):
        """
        Test view query using key parameter as an integer.

        The view used here will generate rows of data where each key will be an
        integer.  Such as:
        {'key': 0, 'id': 'julia000', 'value': 1},
        {'key': 0, 'id': 'julia001', 'value': 1},
        {'key': 1, 'id': 'julia002', 'value': 1},
        {'key': 1, 'id': 'julia003', 'value': 1},
        ...
        {'key': 5, 'id': 'julia010', 'value': 1},
        {'key': 5, 'id': 'julia011', 'value': 1},
        ...
        """
        actual = self.view003(key=5)['rows']
        expected = [{'key': 5, 'id': 'julia010', 'value': 1},
                    {'key': 5, 'id': 'julia011', 'value': 1}]
        self.assertEqual(actual, expected)

    def test_key_str(self):
        """
        Test view query using key parameter as a string.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(key='julia010')['rows']
        expected = [{'key': 'julia010', 'id': 'julia010', 'value': 1}]
        self.assertEqual(actual, expected)

    def test_key_complex(self):
        """
        Test view query using key parameter as a complex key.

        The view used here will generate rows of data where each key is a
        complex key.  Such as:
        {'key': ['julia', 0], 'id': 'julia000', 'value': 1},
        {'key': ['julia', 1], 'id': 'julia001', 'value': 1},
        {'key': ['julia', 2], 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view005(key=['julia', 10])['rows']
        expected = [{'key': ['julia', 10], 'id': 'julia010', 'value': 1}]
        self.assertEqual(actual, expected)

    def test_keys_int(self):
        """
        Test view query using keys parameter as a list of integers.

        The view used here will generate rows of data where each key will be an
        integer.  Such as:
        {'key': 0, 'id': 'julia000', 'value': 1},
        {'key': 0, 'id': 'julia001', 'value': 1},
        {'key': 1, 'id': 'julia002', 'value': 1},
        {'key': 1, 'id': 'julia003', 'value': 1},
        ...
        {'key': 5, 'id': 'julia010', 'value': 1},
        {'key': 5, 'id': 'julia011', 'value': 1},
        ...
        """
        actual = self.view003(keys=[10, 20, 30])['rows']
        expected = [{'key': 10, 'id': 'julia020', 'value': 1},
                    {'key': 10, 'id': 'julia021', 'value': 1},
                    {'key': 20, 'id': 'julia040', 'value': 1},
                    {'key': 20, 'id': 'julia041', 'value': 1},
                    {'key': 30, 'id': 'julia060', 'value': 1},
                    {'key': 30, 'id': 'julia061', 'value': 1}]
        self.assertEqual(actual, expected)

    def test_keys_str(self):
        """
        Test view query using keys parameter as a list of strings.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(keys=['julia010', 'julia020', 'julia030'])['rows']
        expected = [{'key': 'julia010', 'id': 'julia010', 'value': 1},
                    {'key': 'julia020', 'id': 'julia020', 'value': 1},
                    {'key': 'julia030', 'id': 'julia030', 'value': 1}]
        self.assertEqual(actual, expected)

    def test_keys_complex(self):
        """
        Test view query using keys parameter as a list of complex keys.

        The view used here will generate rows of data where each key is a
        complex key.  Such as:
        {'key': ['julia', 0], 'id': 'julia000', 'value': 1},
        {'key': ['julia', 1], 'id': 'julia001', 'value': 1},
        {'key': ['julia', 2], 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view005(keys=[['julia', 10], ['julia', 20], ['julia', 30]])['rows']
        expected = [{'key': ['julia', 10], 'id': 'julia010', 'value': 1},
                    {'key': ['julia', 20], 'id': 'julia020', 'value': 1},
                    {'key': ['julia', 30], 'id': 'julia030', 'value': 1}]
        self.assertEqual(actual, expected)

    def test_limit(self):
        """
        Test view query using the limit parameter.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(limit=10)['rows']
        expected = [{'key': 'julia{0:03d}'.format(x),
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10)]
        self.assertEqual(actual, expected)

    def test_reduce_true(self):
        """
        Test view query using the reduce parameter set to True.

        The view used here along with reduce=True will generate a row of
        data containing the count of documents that match the query.  Such as:
        {'key': None, 'value': 100}
        """
        actual = self.view004(reduce=True)['rows']
        self.assertEqual(actual, [{'key': None, 'value': 100}])

    def test_reduce_false(self):
        """
        Test view query using the reduce parameter set to False.

        The view used here along with reduce=False will generate rows of data
        where each key will be an integer.  Such as:
        {'key': 0, 'id': 'julia000', 'value': 1},
        {'key': 0, 'id': 'julia001', 'value': 1},
        {'key': 1, 'id': 'julia002', 'value': 1},
        {'key': 1, 'id': 'julia003', 'value': 1},
        ...
        {'key': 5, 'id': 'julia010', 'value': 1},
        {'key': 5, 'id': 'julia011', 'value': 1},
        ...
        """
        actual = self.view004(reduce=False)['rows']
        expected = [{'key': x // 2,
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(100)]
        self.assertEqual(len(actual), 100)
        self.assertEqual(len(expected), 100)
        self.assertEqual(actual, expected)

    def test_skip(self):
        """
        Test view query using the skip parameter.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(skip=10)['rows']
        expected = [{'key': 'julia{0:03d}'.format(x),
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10, 100)]
        self.assertEqual(actual, expected)

    def test_stale_ok(self):
        """
        Test view query using the stale parameter set to ok.

        Since there is no way to know whether the view will return a stale
        response or not the test here focuses on ensuring that the call itself
        is successful.
        """
        try:
            self.view001(stale='ok')
        except Exception as err:
            self.fail('An unexpected error was encountered: '+str(err))

    def test_stale_update_after(self):
        """
        Test view query using the stale parameter set to update_after.

        Since there is no way to know whether the view will return a stale
        response or not the test here focuses on ensuring that the call itself
        is successful.
        """
        try:
            self.view001(stale='update_after')
        except Exception as err:
            self.fail('An unexpected error was encountered:' +str(err))
            
    def test_stable_true(self):
        """
        Test view query using the stable parameter set to true

        
        Since there is no way to know whether the view will return a response from a stable set of
        shards or not the test here focuses on ensuring that the call itself is successful.

        """
        try:
            self.view001(stable=True)
        except Exception as err:
            self.fail('An unexpected error was encountered: '+str(err))

    def test_stable_update_lazy(self):
        """
        Test view query using the update parameter set to lazy

        Since there is no way to know whether the view will update lazily or not the test here
        focuses on ensuring that the call itself is successful.

        """
        try:
            self.view001(update='lazy')
        except Exception as err:
            self.fail('An unexpected error was encountered: '+str(err))

    def test_stable_update_true(self):
        """
        Test view query using the update parameter set to true

        Since there is no way to know whether the view will update or not the test here focuses on
        ensuring that the call itself is successful.

        """
        try:
            self.view001(update='true')
        except Exception as err:
            self.fail('An unexpected error was encountered: '+str(err))
                        
    def test_startkey_int(self):
        """
        Test view query using startkey parameter as an integer.

        The view used here will generate rows of data where each key will be an
        integer.  Such as:
        {'key': 0, 'id': 'julia000', 'value': 1},
        {'key': 0, 'id': 'julia001', 'value': 1},
        {'key': 1, 'id': 'julia002', 'value': 1},
        {'key': 1, 'id': 'julia003', 'value': 1},
        ...
        {'key': 5, 'id': 'julia010', 'value': 1},
        {'key': 5, 'id': 'julia011', 'value': 1},
        ...
        """
        actual = self.view003(startkey=5)['rows']
        expected = [{'key': x // 2,
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10, 100)]
        self.assertEqual(len(actual), 90)
        self.assertEqual(len(expected), 90)
        self.assertEqual(actual, expected)

    def test_startkey_str(self):
        """
        Test view query using startkey parameter as a string.

        The view used here will generate rows of data where each key will equal
        the document id.  Such as:
        {'key': 'julia000', 'id': 'julia000', 'value': 1},
        {'key': 'julia001', 'id': 'julia001', 'value': 1},
        {'key': 'julia002', 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view001(startkey='julia010')['rows']
        expected = [{'key': 'julia{0:03d}'.format(x),
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10, 100)]
        self.assertEqual(len(actual), 90)
        self.assertEqual(len(expected), 90)
        self.assertEqual(actual, expected)

    def test_startkey_complex(self):
        """
        Test view query using startkey parameter as a complex key.

        The view used here will generate rows of data where each key is a
        complex key.  Such as:
        {'key': ['julia', 0], 'id': 'julia000', 'value': 1},
        {'key': ['julia', 1], 'id': 'julia001', 'value': 1},
        {'key': ['julia', 2], 'id': 'julia002', 'value': 1},
        ...
        """
        actual = self.view005(startkey=['julia', 10])['rows']
        expected = [{'key': ['julia', x],
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(10, 100)]
        self.assertEqual(len(actual), 90)
        self.assertEqual(len(expected), 90)
        self.assertEqual(actual, expected)

    def test_startkey_docid(self):
        """
        Test view query using startkey_docid parameter.

        The view used here will generate rows of data where each key will have
        two ids associated with it.  Such as:
        {'key': 0, 'id': 'julia000', 'value': 1},
        {'key': 0, 'id': 'julia001', 'value': 1},
        {'key': 1, 'id': 'julia002', 'value': 1},
        {'key': 1, 'id': 'julia003', 'value': 1},
        ...
        {'key': 5, 'id': 'julia010', 'value': 1},
        {'key': 5, 'id': 'julia011', 'value': 1},
        ...
        """
        # Ensure that only rows of data starting at the second document 
        # where the key is 5 are returned.
        actual = self.view003(startkey_docid='julia011', startkey=5)['rows']
        expected = [{'key': x // 2,
                     'id': 'julia{0:03d}'.format(x),
                     'value': 1} for x in range(11, 100)]
        self.assertEqual(len(actual), 89)
        self.assertEqual(len(expected), 89)
        self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()
