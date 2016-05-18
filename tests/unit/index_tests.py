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
Unit tests for the Index module.  IndexTests and TextIndexTests are tested
against Cloudant only.

See configuration options for environment variables in unit_t_db_base
module docstring.

"""
from __future__ import absolute_import

import unittest
import mock
import os
import posixpath
import requests

from cloudant._common_util import _Code
from cloudant.index import Index, TextIndex, SpecialIndex, SearchIndex
from cloudant.query import Query
from cloudant.view import QueryIndexView
from cloudant.design_document import DesignDocument
from cloudant.document import Document
from cloudant.error import CloudantArgumentError, CloudantException

from .. import PY2
from .unit_t_db_base import UnitTestDbBase

@unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is not None,
    'Skipping Cloudant Index tests'
    )
class IndexTests(UnitTestDbBase):
    """
    Index unit tests
    """
    def setUp(self):
        """
        Set up test attributes
        """
        super(IndexTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(IndexTests, self).tearDown()

    def test_constructor_with_args(self):
        """
        Test instantiating an Index by passing in arguments.  As a side effect
        this test also tests the design_document_id, name, type, and definition
        property methods.
        """
        index = Index(self.db, 'ddoc-id', 'index-name', foo={'bar': 'baz'})
        self.assertIsInstance(index, Index)
        self.assertEqual(index.design_document_id, 'ddoc-id')
        self.assertEqual(index.name, 'index-name')
        self.assertEqual(index.type, 'json')
        self.assertEqual(index.definition, {'foo': {'bar': 'baz'}})

    def test_constructor_with_only_a_db(self):
        """
        Test instantiating an Index with a database only.  As a side effect
        this test also tests the design_document_id, name, type, and definition
        property methods.
        """
        index = Index(self.db)
        self.assertIsInstance(index, Index)
        self.assertIsNone(index.design_document_id)
        self.assertIsNone(index.name)
        self.assertEqual(index.type, 'json')
        self.assertEqual(index.definition, {})

    def test_retrieve_index_url(self):
        """
        Test constructing the Index url
        """
        index = Index(self.db)
        self.assertEqual(
            index.index_url,
            posixpath.join(self.db.database_url, '_index')
        )

    def test_index_to_dictionary(self):
        """
        Test the conversion of an Index object into a dictionary representation
        of that object.
        """
        index = Index(self.db, 'ddoc-id', 'index-name', foo={'bar': 'baz'})
        self.assertEqual(index.as_a_dict(), {
            'ddoc': 'ddoc-id',
            'name': 'index-name',
            'type': 'json',
            'def': {'foo': {'bar': 'baz'}}
        })

    def test_index_as_a_dict_with_none_attributes(self):
        """
        Test the conversion of an Index object that contains attributes set to
        None into a dictionary representation of that object.
        """
        index = Index(self.db)
        self.assertEqual(index.as_a_dict(), {
            'ddoc': None,
            'name': None,
            'type': 'json',
            'def': {}
        })

    def test_create_an_index_using_ddoc_index_name(self):
        """
        Test that a JSON index is created in the remote database.
        """
        index = Index(self.db, 'ddoc001', 'index001', fields=['name', 'age'])
        index.create()
        self.assertEqual(index.design_document_id, '_design/ddoc001')
        self.assertEqual(index.name, 'index001')
        with DesignDocument(self.db, index.design_document_id) as ddoc:
            self.assertEqual(ddoc['language'], 'query')
            self.assertListEqual(list(ddoc['views'].keys()), ['index001'])
            self.assertIsInstance(ddoc.get_view('index001'), QueryIndexView)
            self.assertTrue(ddoc['_rev'].startswith('1-'))
            self.assertEqual(ddoc,
                {'_id': '_design/ddoc001',
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'views': {'index001': {'map': {'fields': {'name': 'asc', 
                                                           'age': 'asc'}},
                                        'reduce': '_count',
                                        'options': {'def': {'fields': ['name',
                                                                       'age']},
                                                    'w': 2}}}}
            )

    def test_create_an_index_without_ddoc_index_name(self):
        """
        Test that a JSON index is created in the remote database.
        """
        index = Index(self.db, fields=['name', 'age'])
        index.create()
        self.assertIsNotNone(index.design_document_id)
        self.assertTrue(index.design_document_id.startswith('_design/'))
        self.assertIsNotNone(index.name)
        with DesignDocument(self.db, index.design_document_id) as ddoc:
            self.assertEqual(ddoc['language'], 'query')
            self.assertListEqual(list(ddoc['views'].keys()), [index.name])
            self.assertIsInstance(ddoc.get_view(index.name), QueryIndexView)
            self.assertTrue(ddoc['_rev'].startswith('1-'))
            self.assertEqual(ddoc,
                {'_id': index.design_document_id,
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'views': {index.name: {'map': {'fields': {'name': 'asc', 
                                                           'age': 'asc'}},
                                        'reduce': '_count',
                                        'options': {'def': {'fields': ['name',
                                                                       'age']},
                                                    'w': 2}}}}
            )

    def test_create_an_index_with_empty_ddoc_index_name(self):
        """
        Test that a JSON index is created in the remote database.
        """
        index = Index(self.db, '', '', fields=['name', 'age'])
        index.create()
        self.assertIsNotNone(index.design_document_id)
        self.assertTrue(index.design_document_id.startswith('_design/'))
        self.assertIsNotNone(index.name)
        with DesignDocument(self.db, index.design_document_id) as ddoc:
            self.assertEqual(ddoc['language'], 'query')
            self.assertListEqual(list(ddoc['views'].keys()), [index.name])
            self.assertIsInstance(ddoc.get_view(index.name), QueryIndexView)
            self.assertTrue(ddoc['_rev'].startswith('1-'))
            self.assertEqual(ddoc,
                {'_id': index.design_document_id,
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'views': {index.name: {'map': {'fields': {'name': 'asc', 
                                                           'age': 'asc'}},
                                        'reduce': '_count',
                                        'options': {'def': {'fields': ['name',
                                                                       'age']},
                                                    'w': 2}}}}
            )

    def test_create_an_index_using_design_prefix(self):
        """
        Test that a JSON index is created correctly in the remote database when
        the ddoc id is already prefixed by '_design/'
        """
        index = Index(self.db, '_design/ddoc001', 'index001', fields=['name', 'age'])
        index.create()
        self.assertEqual(index.design_document_id, '_design/ddoc001')
        self.assertEqual(index.name, 'index001')
        with DesignDocument(self.db, index.design_document_id) as ddoc:
            self.assertEqual(ddoc['language'], 'query')
            self.assertListEqual(list(ddoc['views'].keys()), ['index001'])
            self.assertIsInstance(ddoc.get_view('index001'), QueryIndexView)
            self.assertTrue(ddoc['_rev'].startswith('1-'))
            self.assertEqual(ddoc,
                {'_id': '_design/ddoc001',
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'views': {'index001': {'map': {'fields': {'name': 'asc', 
                                                           'age': 'asc'}},
                                        'reduce': '_count',
                                        'options': {'def': {'fields': ['name',
                                                                       'age']},
                                                    'w': 2}}}}
            )

    def test_create_fails_due_to_ddocid_validation(self):
        """
        Ensure that if the design doc id is not a string the create call fails.
        """
        index = Index(self.db, ['ddoc001'], 'index001', fields=['name', 'age'])
        with self.assertRaises(CloudantArgumentError) as cm:
            index.create()
        err = cm.exception
        self.assertEqual(
            str(err),
            'The design document id: [\'ddoc001\'] is not a string.'
        )

    def test_create_fails_due_to_index_name_validation(self):
        """
        Ensure that if the index name is not a string the create call fails.
        """
        index = Index(self.db, 'ddoc001', ['index001'], fields=['name', 'age'])
        with self.assertRaises(CloudantArgumentError) as cm:
            index.create()
        err = cm.exception
        self.assertEqual(
            str(err),
            'The index name: [\'index001\'] is not a string.'
        )

    def test_create_fails_due_to_def_validation(self):
        """
        Ensure that if the index definition contains anything other than
        "fields" the create call fails.
        """
        index = Index(self.db, fields=['name', 'age'], selector={})
        with self.assertRaises(CloudantArgumentError) as cm:
            index.create()
        err = cm.exception
        self.assertTrue(str(err).endswith(
            'A JSON index requires that only a \'fields\' argument is provided.'))

    def test_deleting_index(self):
        """
        Test that deleting an index works as expected.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        self.assertFalse(ddoc.exists())
        index = Index(self.db, 'ddoc001', 'index001', fields=['name', 'age'])
        index.create()
        self.assertTrue(ddoc.exists())
        index.delete()
        self.assertFalse(ddoc.exists())

    def test_deleting_non_existing_index(self):
        """
        Tests how deleting a non-existing index is handled.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        index = Index(self.db, 'ddoc001', 'index001', fields=['name', 'age'])
        self.assertFalse(ddoc.exists())
        with self.assertRaises(requests.HTTPError) as cm:
            index.delete()
        err = cm.exception
        self.assertEqual(err.response.status_code, 404)

    def test_deleting_index_without_ddoc(self):
        """
        Tests that deleting an index without a ddoc id provided fails as
        expected.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        index = Index(self.db, None, 'index001', fields=['name', 'age'])
        self.assertFalse(ddoc.exists())
        with self.assertRaises(CloudantArgumentError) as cm:
            index.delete()
        err = cm.exception
        self.assertEqual(
            str(err),
            'Deleting an index requires a design document id be provided.'
        )

    def test_deleting_index_without_index_name(self):
        """
        Tests that deleting an index without an index name provided fails as
        expected.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        index = Index(self.db, 'ddoc001', fields=['name', 'age'])
        self.assertFalse(ddoc.exists())
        with self.assertRaises(CloudantArgumentError) as cm:
            index.delete()
        err = cm.exception
        self.assertEqual(
            str(err),
            'Deleting an index requires an index name be provided.'
        )

    def test_index_via_query(self):
        """
        Test that a created index will produce expected query results.
        """
        index = Index(self.db, 'ddoc001', 'index001', fields=['age'])
        index.create()
        self.populate_db_with_documents(100)
        query = Query(self.db)
        resp = query(
            fields=['name', 'age'],
            selector={'age': {'$eq': 6}}
        )
        self.assertEqual(resp['docs'], [{'name': 'julia', 'age': 6}])

    def test_index_usage_via_query(self):
        """
        Test that a query will fail if the indexes that exist do not satisfy the
        query selector.
        """
        index = Index(self.db, 'ddoc001', 'index001', fields=['name'])
        index.create()
        self.populate_db_with_documents(100)
        query = Query(self.db)
        with self.assertRaises(requests.HTTPError) as cm:
            resp = query(
                fields=['name', 'age'],
                selector={'age': {'$eq': 6}}
            )
        err = cm.exception
        self.assertEqual(err.response.status_code, 400)

@unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is not None,
    'Skipping Cloudant Text Index tests'
    )
class TextIndexTests(UnitTestDbBase):
    """
    Search Index unit tests
    """
    def setUp(self):
        """
        Set up test attributes
        """
        super(TextIndexTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(TextIndexTests, self).tearDown()

    def test_constructor_with_args(self):
        """
        Test instantiating a TextIndex by passing in arguments.  As a side effect
        this test also tests the design_document_id, name, type, and definition
        property methods.
        """
        index = TextIndex(self.db, 'ddoc-id', 'index-name', foo={'bar': 'baz'})
        self.assertIsInstance(index, TextIndex)
        self.assertEqual(index.design_document_id, 'ddoc-id')
        self.assertEqual(index.name, 'index-name')
        self.assertEqual(index.type, 'text')
        self.assertEqual(index.definition, {'foo': {'bar': 'baz'}})

    def test_constructor_with_only_a_db(self):
        """
        Test instantiating an TextIndex with a database only.  As a side effect
        this test also tests the design_document_id, name, type, and definition
        property methods.
        """
        index = TextIndex(self.db)
        self.assertIsInstance(index, TextIndex)
        self.assertIsNone(index.design_document_id)
        self.assertIsNone(index.name)
        self.assertEqual(index.type, 'text')
        self.assertEqual(index.definition, {})

    def test_create_a_search_index_no_kwargs(self):
        """
        Test that a TEXT index is created in the remote database.
        """
        index = TextIndex(self.db, 'ddoc001', 'index001')
        index.create()
        self.assertEqual(index.design_document_id, '_design/ddoc001')
        self.assertEqual(index.name, 'index001')
        with DesignDocument(self.db, index.design_document_id) as ddoc:
            self.assertEqual(ddoc['language'], 'query')
            self.assertListEqual(list(ddoc['indexes'].keys()), ['index001'])
            self.assertTrue(ddoc['_rev'].startswith('1-'))
            self.assertEqual(ddoc,
                {'_id': '_design/ddoc001',
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'views': {},
                 'indexes': {'index001': 
                     {'index': {'index_array_lengths': True,
                                'fields': 'all_fields',
                                'default_field': {},
                                'default_analyzer': 'keyword',
                                'selector': {}},
                      'analyzer': {'name': 'perfield',
                                   'default': 'keyword',
                                   'fields': {'$default': 'standard'}}}}}
            )

    def test_create_a_search_index_with_kwargs(self):
        """
        Test that a TEXT index is created in the remote database.
        """
        index = TextIndex(
            self.db,
            'ddoc001',
            'index001',
            fields=[{'name': 'name', 'type':'string'},
                    {'name': 'age', 'type':'number'}],
            selector={},
            default_field={'enabled': True, 'analyzer': 'german'})
        index.create()
        self.assertEqual(index.design_document_id, '_design/ddoc001')
        self.assertEqual(index.name, 'index001')
        with DesignDocument(self.db, index.design_document_id) as ddoc:
            self.assertEqual(ddoc['language'], 'query')
            self.assertListEqual(list(ddoc['indexes'].keys()), ['index001'])
            self.assertTrue(ddoc['_rev'].startswith('1-'))
            self.assertEqual(ddoc,
                {'_id': '_design/ddoc001',
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'views': {},
                 'indexes': {'index001': 
                     {'index': {'index_array_lengths': True,
                                'fields': [{'name': 'name', 'type': 'string'},
                                           {'name': 'age', 'type': 'number'}],
                                'default_field': {'enabled': True,
                                                  'analyzer': 'german'},
                                'default_analyzer': 'keyword',
                                'selector': {}},
                      'analyzer': {'name': 'perfield',
                                   'default': 'keyword',
                                   'fields': {'$default': 'german'}}}}}
            )

    def test_create_a_search_index_invalid_argument(self):
        """
        Test that a TEXT index is not created when an invalid argument is given.
        """
        index = TextIndex(self.db, 'ddoc001', 'index001', foo='bar')
        with self.assertRaises(CloudantArgumentError) as cm:
            index.create()
        err = cm.exception
        self.assertEqual(str(err), 'Invalid argument: foo')

    def test_create_a_search_index_invalid_fields_value(self):
        """
        Test that a TEXT index is not created when an invalid fields value is
        given.
        """
        index = TextIndex(self.db, 'ddoc001', 'index001', fields=5)
        with self.assertRaises(CloudantArgumentError) as cm:
            index.create()
        err = cm.exception
        self.assertEqual(
            str(err),
            'Argument fields is not an instance of expected type: '
            '<{} \'list\'>'.format('type' if PY2 else 'class')
        )

    def test_create_a_search_index_invalid_default_field_value(self):
        """
        Test that a TEXT index is not created when an invalid default_field
        value is given.
        """
        index = TextIndex(self.db, 'ddoc001', 'index001', default_field=5)
        with self.assertRaises(CloudantArgumentError) as cm:
            index.create()
        err = cm.exception
        self.assertEqual(
            str(err),
            'Argument default_field is not an instance of expected type: '
            '<{} \'dict\'>'.format('type' if PY2 else 'class')
        )

    def test_create_a_search_index_invalid_selector_value(self):
        """
        Test that a TEXT index is not created when an invalid selector
        value is given.
        """
        index = TextIndex(self.db, 'ddoc001', 'index001', selector=5)
        with self.assertRaises(CloudantArgumentError) as cm:
            index.create()
        err = cm.exception
        self.assertEqual(
            str(err),
            'Argument selector is not an instance of expected type: '
            '<{} \'dict\'>'.format('type' if PY2 else 'class')
        )

    def test_search_index_via_query(self):
        """
        Test that a created TEXT index will produce expected query results.
        """
        index = TextIndex(self.db, 'ddoc001', 'index001')
        index.create()
        self.populate_db_with_documents(100)
        with Document(self.db, 'julia006') as doc:
            doc['name'] = 'julia isabel'
        query = Query(self.db)
        resp = query(
            fields=['name', 'age'],
            selector={'$text': 'isabel'}
        )
        self.assertEqual(resp['docs'], [{'name': 'julia isabel', 'age': 6}])

class SpecialIndexTests(unittest.TestCase):
    """
    Special Index unit tests
    """
    def setUp(self):
        """
        Set up test attributes
        """
        self.db = mock.Mock()
        self.db.r_session = 'mocked-session'
        self.db.database_url = 'http://mocked.url.com/my_db'

    def test_constructor(self):
        """
        Test that the constructor instantiates a SpecialIndex object.
        """
        index = SpecialIndex(self.db, fields=[{'_id': 'asc'}])
        self.assertIsInstance(index, SpecialIndex)
        self.assertEqual(index.as_a_dict(), {
            'ddoc': None,
            'name': '_all_docs',
            'type': 'special',
            'def': {'fields': [{'_id': 'asc'}]}})

    def test_create_disabled(self):
        """
        Test that the SpecialIndex create method is disabled.
        """
        index = SpecialIndex(self.db, fields=[{'_id': 'asc'}])
        with self.assertRaises(CloudantException) as cm:
            index.create()
        err = cm.exception
        self.assertEqual(
            str(err),
            'Creating the \"special\" index is not allowed.'
        )

    def test_delete_disabled(self):
        """
        Test that the SpecialIndex delete method is disabled.
        """
        index = SpecialIndex(self.db, fields=[{'_id': 'asc'}])
        with self.assertRaises(CloudantException) as cm:
            index.delete()
        err = cm.exception
        self.assertEqual(
            str(err),
            'Deleting the \"special\" index is not allowed.'
        )

@unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is not None,
    'Skipping Cloudant Search Index tests'
    )
class SearchIndexTests(UnitTestDbBase):
    """
    Search index unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(SearchIndexTests, self).setUp()
        self.db_set_up()
        self.create_search_index()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(SearchIndexTests, self).tearDown()

    def test_constructor(self):
        """
        Test instantiating a SearchIndex
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        search = SearchIndex(
            ddoc,
            'searchindex001',
            'function (doc) { index("default", doc._id); }}'
            )
        self.assertEqual(search.design_doc, ddoc)
        self.assertEqual(search.index_name, 'searchindex001')
        self.assertIsInstance(search['index'], _Code)
        self.assertEqual(
            search['index'],
            'function (doc) { index("default", doc._id); }}'
        )
        self.assertEqual(
            search['analyzer'],
            'standard'
        )

        self.assertEqual(search, {
            'index': 'function (doc) { index("default", doc._id); }}',
            'analyzer': 'standard'
        })

    def test_index_setter(self):
        """
        Test that the search index setter works
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        search = SearchIndex(ddoc, 'searchindex001')
        self.assertIsNone(search.get('index'))
        search.index = 'function (doc) { index("default", doc._id); }}'
        self.assertEqual(
            search.get('index'),
            'function (doc) { index("default", doc._id); }}'
        )

    def test_index_getter(self):
        """
        Test that the search index getter works
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        search = SearchIndex(ddoc, 'searchindex001')
        self.assertIsNone(search.index)
        search.index = 'function (doc) { index("default", doc._id); }}'
        self.assertIsInstance(search.index, _Code)
        self.assertEqual(search.index,
                         'function (doc) { index("default", doc._id); }}')

    def test_analyzer_setter(self):
        """
        Test that the analyzer setter works
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        search = SearchIndex(ddoc, 'searchindex001')
        self.assertEqual(search.get('analyzer'), 'standard')
        search.analyzer = 'simple'
        self.assertEqual(search.get('analyzer'), 'simple')

    def test_analyzer_getter(self):
        """
        Test that the analyzer getter works
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        search = SearchIndex(ddoc, 'searchindex001')
        self.assertEqual(search.analyzer, 'standard')
        search.analyzer = {
            "name": "perfield", "default": "english",
            "fields": {
                "spanish": "spanish",
                "german": "german"
            }
        }
        self.assertEqual(search.analyzer,
        {
            "name": "perfield", "default": "english",
            "fields": {
                "spanish": "spanish",
                "german": "german"
            }
        })

    def test_retrieve_search_query_url(self):
        """
        Test constructing the search query test url
        """
        search = SearchIndex(self.ddoc, 'searchindex001')
        self.assertEqual(
            search.url,
            '/'.join([self.ddoc.document_url,
                      '_search',
                      'searchindex001'])
        )

    def test_callable_with_invalid_argument(self):
        """
        Test Search __call__ by passing in invalid arguments
        """
        search = SearchIndex(self.ddoc, 'searchindex001')
        try:
            search(foo={'bar': 'baz'})
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(str(err), 'Invalid argument: foo')

    def test_callable_with_invalid_value_types(self):
        """
        Test Search __call__ by passing in invalid value types for
        query parameters
        """
        test_data = [
            {'bookmark': 1},                    # Should be a basestring
            {'counts': 'blah'},                 # Should be a list
            {'drilldown': 'blah'},              # Should be a list
            {'group_field': ['blah']},          # Should be an basestring
            {'group_limit': 'int'},             # Should be an int
            {'group_sort': 'blah'},             # Should be a list
            {'include_docs': 'blah'},           # Should be an boolean
            {'limit': 'blah'},                  # Should be an int
            {'query': ['blah']},                # Should be a basestring or int
            {'ranges': 1},                      # Should be a dict
            {'sort': 10},                       # Should be a basestring or list
            {'stale': ['blah']},                # Should be a basestring
            {'highlight_fields': 'blah'},       # Should be a list
            {'highlight_pre_tag': ['blah']},    # Should be a basestring
            {'highlight_post_tag': 1},          # Should be a basestring
            {'highlight_number': ['int']},      # Should be an int
            {'highlight_size': 'blah'},         # Should be an int
            {'include_fields': 'list'},         # Should be a list
        ]

        for argument in test_data:
            search = SearchIndex(self.ddoc, 'searchindex001')
            try:
                search(**argument)
                self.fail('Above statement should raise an Exception')
            except CloudantArgumentError as err:
                self.assertTrue(str(err).startswith(
                    'Argument {0} is not an instance of expected type:'.format(
                        list(argument.keys())[0]
                    )
                ))

    def test_callable_without_query(self):
        """
        Test Search __call__ without providing a search query
        """
        search = SearchIndex(self.ddoc, 'searchindex001')
        try:
            search(limit=10, include_docs=True)
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(
                str(err),
                'Null value or empty lucene search syntax in '
                'the query parameter. Add a search query and retry.'
            )

    def test_callable_with_empty_query(self):
        """
        Test Search __call__ without providing a search query
        """
        search = SearchIndex(self.ddoc, 'searchindex001')
        try:
            search(query='')
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(
                str(err),
                'Null value or empty lucene search syntax in '
                'the query parameter. Add a search query and retry.'
            )

    def test_callable_executes_search_query(self):
        """
        Test Search __call__ executes a search query
        """
        self.populate_db_with_documents(100)
        search = SearchIndex(self.ddoc, 'searchindex001')
        resp = search(
            # Lucene search query
            query='julia*',
            limit=5,
            include_docs=True
        )
        self.assertEqual(len(resp['rows']), 5)
        self.assertEqual(resp['total_rows'], 100)
        for row in resp['rows']:
            self.assertIsNotNone(row['fields'])
            self.assertTrue(row['id'].startswith('julia0'))
            self.assertIsNotNone(row['order'])
            self.assertIsNotNone(row['doc'])

    def test_callable_executes_search_query_with_group_option(self):
        """
        Test Search __call__ executes a search query with grouping parameters.
        """
        self.populate_db_with_documents(100)
        search = SearchIndex(self.ddoc, 'searchindex001')
        resp = search(
            # Lucene search query
            query='name:julia*',
            group_field='_id',
            group_limit=5,
        )
        # for group parameter options, 'rows' results are within 'groups' key
        self.assertEqual(len(resp['groups']), 5)
        self.assertEqual(resp['total_rows'], 100)
        for group in resp['groups']:
            for row in group['rows']:
                self.assertEqual(row['fields'], {u'name': u'julia'})
                self.assertTrue(row['id'].startswith('julia0'))
                self.assertIsNotNone(row['order'])
            self.assertEqual(group['total_rows'], 1)
            self.assertIsNotNone(group['by'])

if __name__ == '__main__':
    unittest.main()
