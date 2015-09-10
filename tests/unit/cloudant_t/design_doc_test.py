#!/usr/bin/env python
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
        with mock.patch('cloudant.design_document.DesignDocument.save') as mock_save:
            ddoc = DesignDocument(mock_database, '_design/unittest')
            ddoc.add_view('view1', "MAP")
            self.failUnless('view1' in ddoc['views'])
            self.assertEqual(ddoc['views']['view1'].map, 'MAP')
            self.assertEqual(ddoc['views']['view1'].reduce, None)
            self.failUnless(mock_save.called)

    def test_existing_ddoc_add_view(self):
        mock_database = mock.Mock()
        with mock.patch('cloudant.design_document.DesignDocument.save') as mock_save:
            ddoc = DesignDocument(mock_database, '_design/unittest')
            ddoc['views'] = {
                'view1': {'map': "MAP", 'reduce': 'REDUCE'}
            }
            ddoc.add_view('view2', "MAP2")
            self.failUnless('view2' in ddoc['views'])
            self.assertEqual(ddoc['views']['view2'].map, 'MAP2')
            self.assertEqual(ddoc['views']['view2'].reduce, None)
            self.failUnless(mock_save.called)

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
