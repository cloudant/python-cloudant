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

from cloudant.design_document import DesignDocument
from cloudant.views import View
from cloudant.errors import CloudantArgumentError

from unit_t_db_base import UnitTestDbBase

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
        self.assertEqual(ddoc.get('views').keys(), ['view001'])
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
        except CloudantArgumentError, err:
            self.assertEqual(
                str(err),
                'View view001 already exists in this design doc'
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
        except CloudantArgumentError, err:
            self.assertEqual(
                str(err),
                'View view001 does not exist in this design doc'
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

    def test_fetch(self):
        """
        Ensure that the document fetch from the database returns the
        DesignDocument format as expected.
        """
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        view_map = 'function (doc) {\n  emit(doc._id, 1);\n}'
        view_reduce = '_count'
        ddoc.add_view('view001', view_map)
        ddoc.add_view('view002', view_map, view_reduce)
        ddoc.add_view('view003', view_map)
        ddoc.save()
        ddoc_remote = DesignDocument(self.db, '_design/ddoc001')
        self.assertNotEqual(ddoc_remote, ddoc)
        ddoc_remote.fetch()
        self.assertEqual(ddoc_remote, ddoc)
        self.assertEqual(len(ddoc_remote['views']), 3)
        reduce_count = 0
        for x in xrange(1, 4):
            name = 'view{0:03d}'.format(x)
            view = ddoc_remote['views'][name]
            self.assertIsInstance(view, View)
            self.assertEqual(view.map, view_map)
            if name == 'view002':
                reduce_count += 1
                self.assertEqual(view.reduce, view_reduce)
            else:
                self.assertIsNone(view.reduce)
        self.assertEqual(reduce_count, 1)

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
        except NotImplementedError, err:
            self.assertEqual(str(err), '_info not yet implemented')

if __name__ == '__main__':
    unittest.main()
