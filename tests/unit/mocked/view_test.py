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
_view_test_

view module unit tests

"""
import mock
import unittest

from cloudant.view import Code, View
from cloudant.design_document import DesignDocument
from cloudant.result import Result


class CodeTests(unittest.TestCase):
    """tests for cloudant.view.Code, not much to test here yet..."""
    def test_code(self):
        """test instantiation/manipulation"""
        c = Code("function(doc){emit(doc._id, 1)}")


class ViewTests(unittest.TestCase):
    """Tests for View class"""
    def setUp(self):
        self.map_func = "function(doc){emit(doc._id, 1)}"
        self.reduce_func = "_sum"

    def test_view_class(self):
        """test various methods of instantiation and properties"""
        ddoc = DesignDocument(mock.Mock(), "_design/tests")
        view1 = View(ddoc, "view1", map_func=self.map_func, 
            reduce_func=self.reduce_func)
        view2 = View(ddoc, "view2", map_func=self.map_func)
        view3 = View(ddoc, "view1", map_func=Code(self.map_func), 
            reduce_func=Code(self.reduce_func))
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
        db.database_name = 'unittest'
        ddoc = DesignDocument(db, "_design/tests")
        ddoc._database_host = "https://bob.cloudant.com"
        view1 = View(ddoc, "view1", map_func=self.map_func)

        self.assertEqual(
            view1.url,
            "https://bob.cloudant.com/unittest/_design/tests/_view/view1"
        )

    def test_view_context(self):
        db = mock.Mock()
        db.database_name = 'unittest'
        ddoc = DesignDocument(db, "_design/tests")
        ddoc._database_host = "https://bob.cloudant.com"
        view1 = View(ddoc, "view1", map_func=self.map_func)

        with view1.custom_result() as v:
            self.assertTrue(isinstance(v, Result))


if __name__ == '__main__':
    unittest.main()
