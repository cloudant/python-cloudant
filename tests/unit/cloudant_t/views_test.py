#!/usr/bin/env python
"""
_views_test_

"""
import mock
import unittest

from cloudant.views import Code, View, DesignDocument
from cloudant.result import Result
from cloudant.document import Document


class CodeTests(unittest.TestCase):
    """tests for cloudant.views.Code, not much to test here yet..."""
    def test_code(self):
        """test instantiation/manipulation"""
        c = Code("function(doc){emit(doc._id, 1)}")


class ViewTests(unittest.TestCase):
    """tests for View class"""
    def setUp(self):
        self.map_func = "function(doc){emit(doc._id, 1)}"
        self.reduce_func = "_sum"

    def test_view_class(self):
        """test various methods of instantiation and properties"""
        ddoc = DesignDocument(mock.Mock(), "_design/tests")
        view1 = View(ddoc, "view1", map_func=self.map_func, reduce_func=self.reduce_func)
        view2 = View(ddoc, "view2", map_func=self.map_func)
        view3 = View(ddoc, "view1", map_func=Code(self.map_func), reduce_func=Code(self.reduce_func))
        view4 = View(ddoc, "view1", map_func=Code(self.map_func))

        self.assertEqual(view1.map, Code(self.map_func))
        self.assertEqual(view1.reduce, Code(self.reduce_func))
        self.assertEqual(view2.map, Code(self.map_func))
        self.assertEqual(view2.reduce, None)
        self.assertEqual(view3.map, Code(self.map_func))
        self.assertEqual(view3.reduce, Code(self.reduce_func))
        self.assertEqual(view4.map, Code(self.map_func))
        self.assertEqual(view4.reduce, None)

        view5 = View(ddoc, "view5")
        self.assertEqual(view5.map, None)
        self.assertEqual(view5.reduce, None)
        view5.map = self.map_func
        self.assertEqual(view5.map, Code(self.map_func))
        view5.reduce = self.reduce_func
        self.assertEqual(view5.reduce, Code(self.reduce_func))

    def test_view_access(self):
        """
        _test_view_access_

        Test accessing the data via the view

        """
        db = mock.Mock()
        db._database_name = 'unittest'
        ddoc = DesignDocument(db, "_design/tests")
        ddoc._database_host = "https://bob.cloudant.com"
        view1 = View(ddoc, "view1", map_func=self.map_func)

        self.assertEqual(
            view1.url,
            "https://bob.cloudant.com/unittest/_design/tests/_view/view1"
        )

    def test_view_context(self):
        db = mock.Mock()
        db._database_name = 'unittest'
        ddoc = DesignDocument(db, "_design/tests")
        ddoc._database_host = "https://bob.cloudant.com"
        view1 = View(ddoc, "view1", map_func=self.map_func)

        with view1.custom_result() as v:
            self.failUnless(isinstance(v, Result))


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
        views = [ x for _,x in ddoc.iterviews() ]
        self.assertEqual(len(views), 1)
        view = views[0]
        self.failUnless('view1' in view)
        self.assertEqual(view['view1']['map'], 'MAP')
        self.assertEqual(view['view1']['reduce'], 'REDUCE')
        self.failUnless('view1' in ddoc.views)

    def test_ddoc_add_view(self):
        mock_database = mock.Mock()
        with mock.patch('cloudant.views.DesignDocument.save') as mock_save:
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
