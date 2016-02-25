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
_design_document_tests_

design_document module - Unit tests for the DesignDocument class

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest

from cloudant.document import Document 
from cloudant.design_document import DesignDocument
from cloudant.views import View, QueryIndexView
from cloudant.errors import CloudantArgumentError, CloudantException

from .unit_t_db_base import UnitTestDbBase

class DesignDocumentTests(UnitTestDbBase):
    """
    DesignDocument unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(DesignDocumentTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(DesignDocumentTests, self).tearDown()

    def test_constructor_with_docid(self):
        """
        Test instantiating a DesignDocument providing an id
        not prefaced with '_design/'
        """
        ddoc = DesignDocument(self.db, 'ddoc001')
        self.assertIsInstance(ddoc, DesignDocument)
        self.assertEqual(ddoc.get('_id'), '_design/ddoc001')
        self.assertEqual(ddoc.get('views'), {})

    def test_constructor_with_design_docid(self):
        """
        Test instantiating a DesignDocument providing an id
        prefaced with '_design/'
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        self.assertIsInstance(ddoc, DesignDocument)
        self.assertEqual(ddoc.get('_id'), '_design/ddoc001')
        self.assertEqual(ddoc.get('views'), {})

    def test_constructor_without_docid(self):
        """
        Test instantiating a DesignDocument without providing an id
        """
        ddoc = DesignDocument(self.db)
        self.assertIsInstance(ddoc, DesignDocument)
        self.assertIsNone(ddoc.get('_id'))
        self.assertEqual(ddoc.get('views'), {})

    def test_create_design_document_with_docid_encoded_url(self):
        """
        Test creating a design document providing an id that has an encoded url
        """
        ddoc = DesignDocument(self.db, '_design/http://example.com')
        self.assertFalse(ddoc.exists())
        self.assertIsNone(ddoc.get('_rev'))
        ddoc.create()
        self.assertTrue(ddoc.exists())
        self.assertTrue(ddoc.get('_rev').startswith('1-'))

    def test_fetch_existing_design_document_with_docid_encoded_url(self):
        """
        Test fetching design document content from an existing document where
        the document id requires an encoded url
        """
        ddoc = DesignDocument(self.db, '_design/http://example.com')
        ddoc.create()
        new_ddoc = DesignDocument(self.db, '_design/http://example.com')
        new_ddoc.fetch()
        self.assertEqual(new_ddoc, ddoc)

    def test_update_design_document_with_encoded_url(self):
        """
        Test that updating a design document where the document id requires that
        the document url be encoded is successful.
        """
        # First create the design document
        ddoc = DesignDocument(self.db, '_design/http://example.com')
        ddoc.save()
        # Now test that the design document gets updated
        ddoc.save()
        self.assertTrue(ddoc['_rev'].startswith('2-'))
        remote_ddoc = DesignDocument(self.db, '_design/http://example.com')
        remote_ddoc.fetch()
        self.assertEqual(remote_ddoc, ddoc)

    def test_delete_design_document_success_with_encoded_url(self):
        """
        Test that we can remove a design document from the remote
        database successfully when the document id requires an encoded url.
        """
        ddoc = DesignDocument(self.db, '_design/http://example.com')
        ddoc.create()
        self.assertTrue(ddoc.exists())
        ddoc.delete()
        self.assertFalse(ddoc.exists())
        self.assertEqual(ddoc, {'_id': '_design/http://example.com'})

    def test_add_a_view(self):
        """
        Test that adding a view adds a View object to
        the DesignDocument dictionary.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        self.assertEqual(ddoc.get('views'), {})
        ddoc.add_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        self.assertListEqual(list(ddoc.get('views').keys()), ['view001'])
        self.assertIsInstance(ddoc.get('views')['view001'], View)
        self.assertEqual(
            ddoc.get('views')['view001'],
            {'map': 'function (doc) {\n  emit(doc._id, 1);\n}'}
        )

    def test_adding_existing_view(self):
        """
        Test that adding an existing view fails as expected.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.add_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        try:
            ddoc.add_view('view001', 'function (doc) {\n  emit(doc._id, 2);\n}')
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(
                str(err),
                'View view001 already exists in this design doc'
            )

    def test_adding_query_index_view(self):
        """
        Test that adding a query index view fails as expected.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc['language'] = 'query'
        with self.assertRaises(CloudantException) as cm:
            ddoc.add_view('view001', {'foo': 'bar'})
        err = cm.exception
        self.assertEqual(
            str(err),
            'Cannot add a MapReduce view to a '
            'design document for query indexes.'
        )

    def test_update_a_view(self):
        """
        Test that updating a view updates the contents of the correct
        View object in the DesignDocument dictionary.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.add_view('view001', 'not-a-valid-map-function')
        self.assertEqual(
            ddoc.get('views')['view001'],
            {'map': 'not-a-valid-map-function'}
        )
        ddoc.update_view(
            'view001',
            'function (doc) {\n  emit(doc._id, 1);\n}'
        )
        self.assertEqual(
            ddoc.get('views')['view001'],
            {'map': 'function (doc) {\n  emit(doc._id, 1);\n}'}
        )

    def test_update_non_existing_view(self):
        """
        Test that updating a non-existing view fails as expected.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        try:
            ddoc.update_view(
                'view001',
                'function (doc) {\n  emit(doc._id, 1);\n}'
            )
            self.fail('Above statement should raise an Exception')
        except CloudantArgumentError as err:
            self.assertEqual(
                str(err),
                'View view001 does not exist in this design doc'
            )

    def test_update_query_index_view(self):
        """
        Test that updating a query index view fails as expected.
        """
        # This is not the preferred way of dealing with query index
        # views but it works best for this test.
        data = {
            '_id': '_design/ddoc001',
            'language': 'query',
            'views': {
                'view001': {'map': {'fields': {'name': 'asc', 'age': 'asc'}},
                            'reduce': '_count',
                            'options': {'def': {'fields': ['name', 'age']},
                                        'w': 2}
                            }
                    }
        }
        self.db.create_document(data)
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.fetch()
        with self.assertRaises(CloudantException) as cm:
            ddoc.update_view(
                'view001',
                'function (doc) {\n  emit(doc._id, 1);\n}'
            )
        err = cm.exception
        self.assertEqual(
            str(err),
            'Cannot update a query index view using this method.'
        )

    def test_delete_a_view(self):
        """
        Test deleting a view from the DesignDocument dictionary.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.add_view('view001', 'function (doc) {\n  emit(doc._id, 1);\n}')
        self.assertEqual(
            ddoc.get('views')['view001'],
            {'map': 'function (doc) {\n  emit(doc._id, 1);\n}'}
        )
        ddoc.delete_view('view001')
        self.assertEqual(ddoc.get('views'), {})

    def test_delete_a_query_index_view(self):
        """
        Test deleting a query index view fails as expected.
        """
        # This is not the preferred way of dealing with query index
        # views but it works best for this test.
        data = {
            '_id': '_design/ddoc001',
            'language': 'query',
            'views': {
                'view001': {'map': {'fields': {'name': 'asc', 'age': 'asc'}},
                            'reduce': '_count',
                            'options': {'def': {'fields': ['name', 'age']},
                                        'w': 2}
                            }
                    }
        }
        self.db.create_document(data)
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.fetch()
        with self.assertRaises(CloudantException) as cm:
            ddoc.delete_view('view001')
        err = cm.exception
        self.assertEqual(
            str(err),
            'Cannot delete a query index view using this method.'
        )

    def test_fetch_map_reduce(self):
        """
        Ensure that the document fetch from the database returns the
        DesignDocument format as expected when retrieving a design document
        containing MapReduce views.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        view_map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        view_reduce = '_count'
        db_copy = '{0}-copy'.format(self.db.database_name)
        ddoc.add_view('view001', view_map, view_reduce)
        ddoc.add_view('view002', view_map, view_reduce, dbcopy=db_copy)
        ddoc.add_view('view003', view_map)
        ddoc.save()
        ddoc_remote = DesignDocument(self.db, '_design/ddoc001')
        self.assertNotEqual(ddoc_remote, ddoc)
        ddoc_remote.fetch()
        self.assertEqual(ddoc_remote, ddoc)
        self.assertTrue(ddoc_remote['_rev'].startswith('1-'))
        self.assertEqual(ddoc_remote, {
            '_id': '_design/ddoc001',
            '_rev': ddoc['_rev'],
            'views': {
                'view001': {'map': view_map, 'reduce': view_reduce},
                'view002': {'map': view_map, 'reduce': view_reduce, 'dbcopy': db_copy},
                'view003': {'map': view_map}
            }
        })
        self.assertIsInstance(ddoc_remote['views']['view001'], View)
        self.assertIsInstance(ddoc_remote['views']['view002'], View)
        self.assertIsInstance(ddoc_remote['views']['view003'], View)

    def test_fetch_no_views(self):
        """
        Ensure that the document fetched from the database returns the
        DesignDocument format as expected when retrieving a design document
        containing no views.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.save()
        ddoc_remote = DesignDocument(self.db, '_design/ddoc001')
        ddoc_remote.fetch()
        self.assertEqual(set(ddoc_remote.keys()), {'_id', '_rev', 'views'})
        self.assertEqual(ddoc_remote['_id'], '_design/ddoc001')
        self.assertTrue(ddoc_remote['_rev'].startswith('1-'))
        self.assertEqual(ddoc_remote['_rev'], ddoc['_rev'])
        self.assertEqual(ddoc_remote.views, {})

    def test_fetch_query_views(self):
        """
        Ensure that the document fetch from the database returns the
        DesignDocument format as expected when retrieving a design document
        containing query index views.
        """
        # This is not the preferred way of dealing with query index
        # views but it works best for this test.
        data = {
            '_id': '_design/ddoc001',
            'language': 'query',
            'views': {
                'view001': {'map': {'fields': {'name': 'asc', 'age': 'asc'}},
                            'reduce': '_count',
                            'options': {'def': {'fields': ['name', 'age']},
                                        'w': 2}
                            }
                    }
        }
        doc = self.db.create_document(data)
        self.assertIsInstance(doc, Document)
        data['_rev'] = doc['_rev']
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.fetch()
        self.assertIsInstance(ddoc, DesignDocument)
        self.assertEqual(ddoc, data)
        self.assertIsInstance(ddoc['views']['view001'], QueryIndexView)

    def test_fetch_text_indexes(self):
        """
        Ensure that the document fetch from the database returns the
        DesignDocument format as expected when retrieving a design document
        containing query index views.
        """
        # This is not the preferred way of dealing with query index
        # views but it works best for this test.
        data = {
            '_id': '_design/ddoc001',
            'language': 'query',
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
        doc = self.db.create_document(data)
        self.assertIsInstance(doc, Document)
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.fetch()
        self.assertIsInstance(ddoc, DesignDocument)
        data['_rev'] = doc['_rev']
        data['views'] = dict()
        self.assertEqual(ddoc, data)
        self.assertIsInstance(ddoc['indexes']['index001'], dict)

    def test_fetch_text_indexes_and_query_views(self):
        """
        Ensure that the document fetch from the database returns the
        DesignDocument format as expected when retrieving a design document
        containing query index views and text index definitions.
        """
        # This is not the preferred way of dealing with query index
        # views but it works best for this test.
        data = {
            '_id': '_design/ddoc001',
            'language': 'query',
            'views': {
                'view001': {'map': {'fields': {'name': 'asc', 'age': 'asc'}},
                            'reduce': '_count',
                            'options': {'def': {'fields': ['name', 'age']},
                                        'w': 2}
                            }
                    },
            'indexes': {'index001': {
                'index': {'index_array_lengths': True,
                          'fields': [{'name': 'name', 'type': 'string'},
                                     {'name': 'age', 'type': 'number'}],
                          'default_field': {'enabled': True,
                                            'analyzer': 'german'},
                          'default_analyzer': 'keyword',
                          'selector': {}},
                'analyzer': {'name': 'perfield',
                             'default': 'keyword',
                             'fields': {'$default': 'german'}}}}}
        doc = self.db.create_document(data)
        self.assertIsInstance(doc, Document)
        data['_rev'] = doc['_rev']
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.fetch()
        self.assertIsInstance(ddoc, DesignDocument)
        self.assertEqual(ddoc, data)
        self.assertIsInstance(ddoc['indexes']['index001'], dict)
        self.assertIsInstance(ddoc['views']['view001'], QueryIndexView)

    def test_mr_view_save_fails_when_lang_is_query(self):
        """
        Tests that save fails when language is query but views are map reduce
        views.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        view_map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        view_reduce = '_count'
        db_copy = '{0}-copy'.format(self.db.database_name)
        ddoc.add_view('view001', view_map, view_reduce, dbcopy=db_copy)
        ddoc['language'] = 'query'
        with self.assertRaises(CloudantException) as cm:
            ddoc.save()
        err = cm.exception
        self.assertEqual(
            str(err),
            'View view001 must be of type QueryIndexView.'
        )

    def test_mr_view_save_succeeds(self):
        """
        Tests that save succeeds when no language is specified and views are map
        reduce views.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        view_map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        view_reduce = '_count'
        db_copy = '{0}-copy'.format(self.db.database_name)
        ddoc.add_view('view001', view_map, view_reduce, dbcopy=db_copy)
        ddoc.save()
        self.assertTrue(ddoc['_rev'].startswith('1-'))

    def test_cq_view_save_fails_when_lang_is_not_query(self):
        """
        Tests that save fails when language is not query but views are query
        index views.
        """
        # This is not the preferred way of dealing with query index
        # views but it works best for this test.
        data = {
            '_id': '_design/ddoc001',
            'language': 'query',
            'views': {
                'view001': {'map': {'fields': {'name': 'asc', 'age': 'asc'}},
                            'reduce': '_count',
                            'options': {'def': {'fields': ['name', 'age']},
                                        'w': 2}
                            }
                    }
        }
        self.db.create_document(data)
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.fetch()
        with self.assertRaises(CloudantException) as cm:
            ddoc['language'] = 'not-query'
            ddoc.save()
        err = cm.exception
        self.assertEqual(str(err), 'View view001 must be of type View.')

        with self.assertRaises(CloudantException) as cm:
            del ddoc['language']
            ddoc.save()
        err = cm.exception
        self.assertEqual(str(err), 'View view001 must be of type View.')

    def test_cq_view_save_succeeds(self):
        """
        Tests that save succeeds when language is query and views are query
        index views.
        """
        # This is not the preferred way of dealing with query index
        # views but it works best for this test.
        data = {
            '_id': '_design/ddoc001',
            'language': 'query',
            'views': {
                'view001': {'map': {'fields': {'name': 'asc', 'age': 'asc'}},
                            'reduce': '_count',
                            'options': {'def': {'fields': ['name', 'age']},
                                        'w': 2}
                            }
                    }
        }
        self.db.create_document(data)
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.fetch()
        self.assertTrue(ddoc['_rev'].startswith('1-'))
        ddoc.save()
        self.assertTrue(ddoc['_rev'].startswith('2-'))

    def test_save_with_no_views(self):
        """
        Tests the functionality when saving a design document without a view.
        The locally cached DesignDocument should contain an empty views dict
        while the design document saved remotely should not include the empty
        views sub-document.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.save()
        # Ensure that locally cached DesignDocument contains an
        # empty views dict.
        self.assertEqual(set(ddoc.keys()), {'_id', '_rev', 'views'})
        self.assertEqual(ddoc['_id'], '_design/ddoc001')
        self.assertTrue(ddoc['_rev'].startswith('1-'))
        self.assertEqual(ddoc.views, {})
        # Ensure that remotely saved design document does not
        # include a views sub-document.
        resp = self.client.r_session.get(ddoc.document_url)
        raw_ddoc = resp.json()
        self.assertEqual(set(raw_ddoc.keys()), {'_id', '_rev'})
        self.assertEqual(raw_ddoc['_id'], ddoc['_id'])
        self.assertEqual(raw_ddoc['_rev'], ddoc['_rev'])

    def test_setting_id(self):
        """
        Ensure when setting the design document id that it is
        prefaced by '_design/'
        """
        ddoc = DesignDocument(self.db)
        ddoc['_id'] = 'ddoc001'
        self.assertEqual(ddoc['_id'], '_design/ddoc001')
        del ddoc['_id']
        self.assertIsNone(ddoc.get('_id'))
        ddoc['_id'] = '_design/ddoc002'
        self.assertEqual(ddoc['_id'], '_design/ddoc002')

    def test_iterating_over_views(self):
        """
        Test iterating over views within the DesignDocument
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        view_map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        ddoc.add_view('view001', view_map)
        ddoc.add_view('view002', view_map)
        ddoc.add_view('view003', view_map)
        view_names = []
        for view_name, view in ddoc.iterviews():
            self.assertIsInstance(view, View)
            view_names.append(view_name)
        self.assertTrue(
            all(x in view_names for x in ['view001', 'view002', 'view003'])
        )

    def test_list_views(self):
        """
        Test the retrieval of view name list from DesignDocument
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        view_map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        ddoc.add_view('view001', view_map)
        ddoc.add_view('view002', view_map)
        ddoc.add_view('view003', view_map)
        self.assertTrue(
            all(x in ddoc.list_views() for x in [
                'view001',
                'view002',
                'view003'
            ])
        )

    def test_get_view(self):
        """
        Test retrieval of a view from the DesignDocument
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        view_map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        view_reduce = '_count'
        ddoc.add_view('view001', view_map)
        ddoc.add_view('view002', view_map, view_reduce)
        ddoc.add_view('view003', view_map)
        self.assertIsInstance(ddoc.get_view('view002'), View)
        self.assertEqual(
            ddoc.get_view('view002'),
            {
            'map': 'function (doc) {\n  emit(doc._id, 1);\n}',
            'reduce': '_count'
            }
        )

    def test_get_info(self):
        """
        Test that the appropriate "not implemented" exception is raised
        when attempting to execute the .info() method
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        try:
            ddoc.info()
            self.fail('Above statement should raise an Exception')
        except NotImplementedError as err:
            self.assertEqual(str(err), '_info not yet implemented')

if __name__ == '__main__':
    unittest.main()
