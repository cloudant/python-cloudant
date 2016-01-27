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
_end_to_end_example_test_

End to end integration tests

"""
import uuid
import unittest

from cloudant import cloudant, couchdb
from cloudant.credentials import read_dot_cloudant, read_dot_couch

class E2ECouchTest(unittest.TestCase):
    """
    end to end operational test against a couchdb instance
    """
    def setUp(self):
        self.user, self.passwd = read_dot_couch(filename="~/.clou")
        self.dbname = "couch-e2e-test-{0}".format(str(uuid.uuid4()))

    def test_end_to_end(self):
        """
        End to end database and document crud tests

        """
        with couchdb(self.user, self.passwd, url='http://127.0.0.1:5984') as c:
            session = c.session()
            self.assertEqual(session['userCtx']['name'], self.user)

            db = c.create_database(self.dbname)

            try:
                self.assertIn(self.dbname, c)
                self.assertTrue(db.exists())

                # creating docs
                doc1 = db.new_document()
                doc2 = db.create_document({'_id': 'womp', 
                    "testing": "document2"})
                doc3 = db.create_document({"testing": "document3"})

                self.assertIn('_id', doc1)
                self.assertIn('_rev', doc1)
                self.assertIn('_id', doc2)
                self.assertIn('_rev', doc2)
                self.assertIn('_id', doc3)
                self.assertIn('_rev', doc3)

                # verifying access via dict api
                self.assertIn(doc1['_id'], db)
                self.assertIn(doc2['_id'], db)
                self.assertIn(doc3['_id'], db)

                self.assertEqual(db[doc1['_id']], doc1)
                self.assertEqual(db[doc2['_id']], doc2)
                self.assertEqual(db[doc3['_id']], doc3)
                # test working context for updating docs
                with doc2 as working_doc:
                    working_doc['field1'] = [1, 2, 3]
                    working_doc['field2'] = {'a': 'b'}

                self.assertEqual(
                    c[self.dbname]['womp']['field2'],
                    {'a': 'b'}
                )

            finally:
                # remove test database
                c.delete_database(self.dbname)


class E2ECloudantTest(unittest.TestCase):
    """
    starting with a test account, create some
    databases, documents, updates, deletes etc

    """
    def setUp(self):
        self.user, self.passwd = read_dot_cloudant(filename="~/.clou")
        self.dbname = "cloudant-e2e-test-{0}".format(str(uuid.uuid4()))

    def test_end_to_end(self):
        """
        End to end database and document crud tests

        """
        with cloudant(self.user, self.passwd, account=self.user) as c:
            session = c.session()
            self.assertEqual(session['userCtx']['name'], self.user)

            db = c.create_database(self.dbname)

            try:

                self.assertIn(self.dbname, c)
                self.assertTrue(db.exists())

                # creating docs
                doc1 = db.new_document()
                doc2 = db.create_document({'_id': 'womp', 
                    "testing": "document2"})
                doc3 = db.create_document({"testing": "document3"})

                self.assertIn('_id', doc1)
                self.assertIn('_rev', doc1)
                self.assertIn('_id', doc2)
                self.assertIn('_rev', doc2)
                self.assertIn('_id', doc3)
                self.assertIn('_rev', doc3)

                # verifying access via dict api
                self.assertIn(doc1['_id'], db)
                self.assertIn(doc2['_id'], db)
                self.assertIn(doc3['_id'], db)

                self.assertEqual(db[doc1['_id']], doc1)
                self.assertEqual(db[doc2['_id']], doc2)
                self.assertEqual(db[doc3['_id']], doc3)

                # test working context for updating docs
                with doc2 as working_doc:
                    working_doc['field1'] = [1, 2, 3]
                    working_doc['field2'] = {'a': 'b'}

                self.assertEqual(
                    c[self.dbname]['womp']['field2'],
                    {'a': 'b'}
                )

            finally:
                # remove test database
                c.delete_database(self.dbname)



if __name__ == '__main__':
    unittest.main()

