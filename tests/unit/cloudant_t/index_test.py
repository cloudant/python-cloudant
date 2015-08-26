#!/usr/bin/env python
"""
Index unittests

"""
import datetime
import unittest

from cloudant.index import python_to_couch, Index, type_or_none
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
        self.assertRaises(CloudantArgumentError, python_to_couch, {"womp": "womp"})
        self.assertRaises(CloudantArgumentError, python_to_couch, {"group": "womp"})
        self.assertRaises(CloudantArgumentError, python_to_couch, {"stale": "womp"})

        # this datetime triggers an argument conversion error
        self.assertRaises(CloudantArgumentError, python_to_couch, {'endkey': [1,2,3, datetime.datetime.utcnow()]})

    def test_type_or_none(self):
        self.failUnless(type_or_none((int, float), 1))
        self.failUnless(type_or_none((int, float), 1.0))
        self.failUnless(type_or_none((int, float), None))
        self.failUnless(not type_or_none((int, float), "womp"))


class IndexTests(unittest.TestCase):
    """
    tests for Index class
    """
    def test_index_getitem(self):
        ref = mock.Mock()
        ref.return_value = {'rows': [1,2,3]}
        idx = Index(ref)

        # string key:
        self.assertEqual(idx["abc"], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(key='abc'))
        self.assertEqual(idx[["abc", "def"]], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(key=['abc', 'def']))

        # list slice
        self.assertEqual(idx["abc":"def"], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(startkey='abc', endkey='def'))
        self.assertEqual(idx["abc":], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(startkey='abc'))
        self.assertEqual(idx[:"def"], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(endkey='def'))
        self.assertEqual(idx[:], [1,2,3])
        self.assertEqual(ref.call_args, mock.call())

        # int slice
        self.assertEqual(idx[1:100], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(skip=1, limit=99))
        self.assertEqual(idx[1:], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(skip=1))
        self.assertEqual(idx[:100], [1,2,3])
        self.assertEqual(ref.call_args, mock.call(limit=100))

        self.assertRaises(CloudantArgumentError, idx.__getitem__, {})

    def test_iter_method(self):
        """test basics of iter method"""
        ref = mock.Mock()
        ref.side_effect = [{'rows': [1,2,3]}, {'rows': []}]
        idx = Index(ref)
        results = [x for x in idx]
        self.assertEqual(results, [1,2,3])

        run_iter = lambda x: [y for y in x]

        idx = Index(ref, skip=1000)
        self.assertRaises(CloudantArgumentError, run_iter, idx)

        idx = Index(ref, limit=1000)
        self.assertRaises(CloudantArgumentError, run_iter, idx)

    def test_iter_paging(self):
        """iterate with multiple pages of data"""
        ref = mock.Mock()
        ref.side_effect = [
            {'rows': [x for x in range(100)]},
            {'rows': []}
        ]
        idx = Index(ref, page_size=10)
        results = [x for x in idx]
        self.assertEqual(len(results), 100)

if __name__ == '__main__':
    unittest.main()
