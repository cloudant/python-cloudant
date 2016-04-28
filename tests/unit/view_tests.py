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
_view_tests_

view module - Unit tests for the View/QueryIndexView classes

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import mock
import posixpath
import requests
import os

from cloudant.design_document import DesignDocument
from cloudant.view import View, QueryIndexView
from cloudant._common_util import _Code
from cloudant.result import Result
from cloudant.error import CloudantArgumentError, CloudantException

from .unit_t_db_base import UnitTestDbBase

class CodeTests(unittest.TestCase):
    """
    _Code class unit test
    """

    def test_constructor(self):
        """
        Ensure that the _Code class constructor returns a _Code object that
        wraps a Python str
        """
        code = _Code('this is code.')
        self.assertIsInstance(code, _Code)
        self.assertEqual(code, 'this is code.')

class ViewTests(UnitTestDbBase):
    """
    View class unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(ViewTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(ViewTests, self).tearDown()

    def test_constructor(self):
        """
        Test instantiating a View
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        view = View(
            ddoc,
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}',
            '_count',
            dbcopy='{0}-copy'.format(self.db.database_name)
        )
        self.assertEqual(view.design_doc, ddoc)
        self.assertEqual(view.view_name, 'view001')
        self.assertIsInstance(view['map'], _Code)
        self.assertEqual(
            view['map'],
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        self.assertIsInstance(view['reduce'], _Code)
        self.assertEqual(view['reduce'], '_count')
        self.assertEqual(
            view['dbcopy'],
            '{0}-copy'.format(self.db.database_name)
        )
        self.assertEqual(view, {
            'map': 'function (doc) {\n  emit(doc._id, 1);\n}',
            'reduce': '_count',
            'dbcopy': '{0}-copy'.format(self.db.database_name)
        })

    def test_map_setter(self):
        """
        Test that the map setter works
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        view = View(ddoc, 'view001')
        self.assertIsNone(view.get('map'))
        view.map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        self.assertEqual(
            view.get('map'),
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )

    def test_map_getter(self):
        """
        Test that the map getter works
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        view = View(ddoc, 'view001')
        self.assertIsNone(view.map)
        view.map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        self.assertIsInstance(view.map, _Code)
        self.assertEqual(view.map, 'function (doc) {\n  emit(doc._id, 1);\n}')

    def test_reduce_setter(self):
        """
        Test that the reduce setter works
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        view = View(ddoc, 'view001')
        self.assertIsNone(view.get('reduce'))
        view.reduce = '_count'
        self.assertEqual(view.get('reduce'), '_count')

    def test_reduce_getter(self):
        """
        Test that the reduce getter works
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        view = View(ddoc, 'view001')
        self.assertIsNone(view.reduce)
        view.reduce = '_count'
        self.assertIsInstance(view.reduce, _Code)
        self.assertEqual(view.reduce, '_count')

    def test_retrieve_view_url(self):
        """
        Test the retrieval of the View url
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        view = View(ddoc, 'view001')
        self.assertEqual(
            view.url,
            posixpath.join(ddoc.document_url, '_view/view001')
        )

    def test_get_view_callable_raw_json(self):
        """
        Test that the GET request of the View __call__ method that is invoked
        when calling the view object returns the appropriate raw JSON response.
        """
        self.populate_db_with_documents()
        ddoc = DesignDocument(self.db, 'ddoc001')
        ddoc.add_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        ddoc.save()
        view = ddoc.get_view('view001')
        ids = []
        # view(limit=3) calls the view object and passes it the limit parameter
        # where a HTTP GET request is made.
        for row in view(limit=3)['rows']:
            ids.append(row['id'])
        expected = ['julia000', 'julia001', 'julia002']
        self.assertTrue(all(x in ids for x in expected))

    def test_post_view_callable_raw_json(self):
        """
        Using the "keys" parameter test that the POST request of the View
        __call__ method that is invoked when calling the view object returns the
        appropriate raw JSON response.
        """
        # Create 200 documents with ids julia000, julia001, julia002, ..., julia199
        self.populate_db_with_documents(200)
        # Generate keys list for every other document created
        # with ids julia000, julia002, julia004, ..., julia198
        keys_list = ['julia{0:03d}'.format(i) for i in range(0, 200, 2)]
        self.assertEqual(len(keys_list), 100)
        ddoc = DesignDocument(self.db, 'ddoc001')
        ddoc.add_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        ddoc.save()
        view = ddoc.get_view('view001')
        # view(keys=keys_list) calls the view object and passes keys parameter
        ids = [row['id'] for row in view(keys=keys_list)['rows']]
        self.assertEqual(len(ids), 100)
        self.assertTrue(all(x in ids for x in keys_list))

    def test_post_view_callable_raw_json_multiple_params(self):
        """
        Using "keys" and other parameters test that the POST request of the View
        __call__ method that is invoked when calling the view object returns the
        appropriate raw JSON response.
        """
        # Create 200 documents with ids julia000, julia001, julia002, ..., julia199
        self.populate_db_with_documents(200)
        # Generate keys list for every other document created
        # with ids julia000, julia002, julia004, ..., julia198
        keys_list = ['julia{0:03d}'.format(i) for i in range(0, 200, 2)]
        self.assertEqual(len(keys_list), 100)
        ddoc = DesignDocument(self.db, 'ddoc001')
        ddoc.add_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        ddoc.save()
        view = ddoc.get_view('view001')
        # view(keys=keys_list, limit=3) calls the view object and passes keys
        # and limit parameters
        ids = [row['id'] for row in view(keys=keys_list, limit=3)['rows']]
        self.assertTrue(all(x in ids for x in ['julia000', 'julia002', 'julia004']))

    def test_view_callable_view_result(self):
        """
        Test that by referencing the .result attribute the view callable
        method is invoked and the data returned is wrapped as a Result.
        """
        self.populate_db_with_documents()
        ddoc = DesignDocument(self.db, 'ddoc001')
        ddoc.add_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        ddoc.save()
        view = ddoc.get_view('view001')
        rslt = view.result
        self.assertIsInstance(rslt, Result)
        ids = []
        # rslt[:3] limits the Result to the first 3 elements
        for row in rslt[:3]:
            ids.append(row['id'])
        expected = ['julia000', 'julia001', 'julia002']
        self.assertTrue(all(x in ids for x in expected))

    def test_view_callable_with_non_existing_view(self):
        """
        Test error condition when view used does not exist remotely.
        """
        self.populate_db_with_documents()
        # The view "missing-view" does not exist in the remote database
        view = View(
            DesignDocument(self.db, 'ddoc001'),
            'missing-view',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        self.assertIsInstance(view, View)
        try:
            for row in view.result:
                self.fail('Above statement should raise an Exception')
        except requests.HTTPError as err:
            self.assertEqual(err.response.status_code, 404)

    @unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is None,
            'Only execute as part of CouchDB tests')
    def test_view_callable_with_invalid_javascript(self):
        """
        Test error condition when Javascript errors exist.  This test is only
        valid for CouchDB because the map function Javascript is validated on
        the Cloudant server when attempting to save a design document so invalid
        Javascript is not possible there.
        """
        self.populate_db_with_documents()
        ddoc = DesignDocument(self.db, 'ddoc001')
        ddoc.add_view(
            'view001',
            'This is not valid Javascript'
        )
        ddoc.save()
        # Verify that the ddoc and view were saved remotely 
        # along with the invalid Javascript
        del ddoc
        ddoc = DesignDocument(self.db, 'ddoc001')
        ddoc.fetch()
        view = ddoc.get_view('view001')
        self.assertEqual(view.map, 'This is not valid Javascript')
        try:
            for row in view.result:
                self.fail('Above statement should raise an Exception')
        except requests.HTTPError as err:
            self.assertEqual(err.response.status_code, 500)

    def test_custom_result_context_manager(self):
        """
        Test that the context manager for custom results returns
        the expected Results
        """
        self.populate_db_with_documents()
        ddoc = DesignDocument(self.db, 'ddoc001')
        ddoc.add_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        ddoc.save()
        view = ddoc.get_view('view001')
        # Return a custom result by including documents
        with view.custom_result(include_docs=True, reduce=False) as rslt:
            i = 0
            for row in rslt:
                self.assertEqual(row['doc']['_id'], 'julia{0:03d}'.format(i))
                self.assertTrue(row['doc']['_rev'].startswith('1-'))
                self.assertEqual(row['doc']['name'], 'julia')
                self.assertEqual(row['doc']['age'], i)
                i += 1
            self.assertEqual(i, 100)

class QueryIndexViewTests(unittest.TestCase):
    """
    QueryIndexView class unit tests.  These tests use a mocked DesignDocument
    since a QueryIndexView object is not callable so an actual connection
    is not necessary.
    """

    def setUp(self):
        """
        Set up test attributes
        """
        self.ddoc = mock.Mock()
        self.ddoc.r_session = 'mocked-session'
        self.ddoc.document_url = 'http://mock.example.com/my_db/_design/ddoc001'

        self.view = QueryIndexView(
            self.ddoc,
            'view001',
            {'fields': {'name': 'asc', 'age': 'asc'}},
            '_count',
            options = {'def': {'fields': ['name', 'age']}, 'w': 2}
        )

    def test_constructor(self):
        """
        Test constructing a QueryIndexView
        """
        self.assertIsInstance(self.view, QueryIndexView)
        self.assertEqual(self.view.design_doc, self.ddoc)
        self.assertEqual(self.view.view_name, 'view001')
        self.assertIsNone(self.view.result)
        self.assertEqual(self.view, {
            'map': {'fields': {'name': 'asc', 'age': 'asc'}},
            'reduce': '_count',
            'options': {'def': {'fields': ['name', 'age']}, 'w': 2}
        })

    def test_map_getter(self):
        """
        Test that the map getter works
        """
        self.assertEqual(
            self.view.map,
            {'fields': {'name': 'asc', 'age': 'asc'}}
        )
        self.assertEqual(self.view.map, self.view['map'])

    def test_map_setter(self):
        """
        Test that the map setter works
        """
        self.view.map = {'fields': {'name': 'desc', 'age': 'desc'}}
        self.assertEqual(
            self.view.map,
            {'fields': {'name': 'desc', 'age': 'desc'}}
        )
        self.assertEqual(self.view.map, self.view['map'])

    def test_map_setter_failure(self):
        """
        Test that the map setter fails if a dict is not supplied
        """
        try:
            self.view.map = 'function (doc) {\n  emit(doc._id, 1);\n}'
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(
                str(err),
                'The map property must be a dictionary'
            )

    def test_reduce_getter(self):
        """
        Test that the reduce getter works
        """
        self.assertEqual(self.view.reduce, '_count')
        self.assertEqual(self.view.reduce, self.view['reduce'])

    def test_reduce_setter(self):
        """
        Test that the reduce setter works
        """
        self.view.reduce = '_sum'
        self.assertEqual(self.view.reduce, '_sum')
        self.assertEqual(self.view.reduce, self.view['reduce'])

    def test_reduce_setter_failure(self):
        """
        Test that the reduce setter fails if a string is not supplied
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            self.view.reduce = {'_count'}
        err = cm.exception
        self.assertEqual(str(err), 'The reduce property must be a string')

    def test_callable_disabled(self):
        """
        Test that the callable for QueryIndexView does not execute.
        """
        with self.assertRaises(CloudantException) as cm:
            self.view()
        err = cm.exception
        self.assertEqual(
            str(err),
            'A QueryIndexView is not callable.  '
            'If you wish to execute a query '
            'use the database \'get_query_result\' convenience method.'
        )

    def test_custom_result_disabled(self):
        """
        Test that the custom_result context manager for QueryIndexView does not
        execute.
        """
        with self.assertRaises(CloudantException) as cm:
            with self.view.custom_result() as result:
                pass
        err = cm.exception
        self.assertEqual(
            str(err),
            'Cannot create a custom result context manager using a '
            'QueryIndexView.  If you wish to execute a query use the '
            'database \'get_query_result\' convenience method instead.'
        )

if __name__ == '__main__':
    unittest.main()
