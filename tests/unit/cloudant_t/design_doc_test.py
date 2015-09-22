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
_design_doc_test_

"""
import mock
import unittest

from cloudant.design_document import DesignDocument
from cloudant.document import Document


class DesignDocTests(unittest.TestCase):
    """
    tests for design doc object

    """
    @mock.patch.object(Document, 'fetch')
    def test_design_doc(self, mock_fetch):
        """test overridden methods work as expected"""
        mock_database = mock.Mock()
        ddoc = DesignDocument(mock_database, '_design/unittest')
        ddoc['views'] = {
            'view1' : {'map': "MAP", 'reduce': 'REDUCE'}
        }
        ddoc.fetch()

        self.failUnless(mock_fetch.called)
        views = [ x for x in ddoc.iterviews() ]
        self.assertEqual(len(views), 1)
        view = views[0]
        self.failUnless('view1' in view)
        funcs = view[1]
        self.assertEqual(funcs['map'], 'MAP')
        self.assertEqual(funcs['reduce'], 'REDUCE')
        self.failUnless('view1' in ddoc.views)

    def test_new_ddoc_add_view(self):
        mock_database = mock.Mock()
        ddoc = DesignDocument(mock_database, '_design/unittest')
        ddoc.add_view('view1', "MAP")
        self.failUnless('view1' in ddoc['views'])
        self.assertEqual(ddoc['views']['view1'].map, 'MAP')
        self.assertEqual(ddoc['views']['view1'].reduce, None)

    def test_existing_ddoc_add_view(self):
        mock_database = mock.Mock()
        ddoc = DesignDocument(mock_database, '_design/unittest')
        ddoc['views'] = {
           'view1': {'map': "MAP", 'reduce': 'REDUCE'}
        }
        ddoc.add_view('view2', "MAP2")
        self.failUnless('view1' in ddoc['views'])
        self.failUnless('view2' in ddoc['views'])
        self.assertEqual(ddoc['views']['view2'].map, 'MAP2')
        self.assertEqual(ddoc['views']['view2'].reduce, None)

    def test_ddoc_update_view(self):
        mock_database = mock.Mock()
        ddoc = DesignDocument(mock_database, '_design/unittest')
        ddoc.add_view('view1', "MAP", "REDUCE")
        
        ddoc.update_view('view1', "UPDATED_MAP")
        self.failUnless('view1' in ddoc['views'])
        self.assertEqual(ddoc['views']['view1'].map, 'UPDATED_MAP')
        self.assertEqual(ddoc['views']['view1'].reduce, 'REDUCE')

    def test_ddoc_delete_view(self):
        mock_database = mock.Mock()
        ddoc = DesignDocument(mock_database, '_design/unittest')
        ddoc.add_view('view1', "MAP", "REDUCE")
        ddoc.add_view('view2', "MAP", "REDUCE")
        self.failUnless('view1' in ddoc['views'])
        self.failUnless('view2' in ddoc['views'])
        
        ddoc.delete_view('view2')
        self.failUnless('view1' in ddoc['views'])
        self.failUnless('view2' not in ddoc['views'])
        self.assertEqual(ddoc['views']['view1'].map, 'MAP')
        self.assertEqual(ddoc['views']['view1'].reduce, 'REDUCE')

    def test_list_views(self):
        mock_database = mock.Mock()
        ddoc = DesignDocument(mock_database, '_design/unittest')
        ddoc['views'] = {
            'view1': {'map': "MAP", 'reduce': 'REDUCE'},
            'view2': {'map': "MAP", 'reduce': 'REDUCE'},
        }
        self.assertEqual(ddoc.list_views(), ['view1', 'view2'])


if __name__ == '__main__':
    unittest.main()
