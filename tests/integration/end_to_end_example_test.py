#!/usr/bin/env python
"""
E2E Examples Integ test

"""
import uuid
import unittest

from cloudant import cloudant
from cloudant.credentials import read_dot_cloudant

class E2ETest(unittest.TestCase):
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
        with cloudant(self.user, self.passwd) as c:
            session = c.session()
            self.assertEqual(session['userCtx']['name'], self.user)

            db = c.create_database(self.dbname)

            try:

                self.failUnless(self.dbname in c)
                self.failUnless(db.exists())

                # creating docs
                doc1 = db.new_document()
                doc2 = db.create_document({'_id': 'womp', "testing": "document2"})
                doc3 = db.create_document({"testing": "document3"})

                self.failUnless('_id' in doc1)
                self.failUnless('_rev' in doc1)
                self.failUnless('_id' in doc2)
                self.failUnless('_rev' in doc2)
                self.failUnless('_id' in doc3)
                self.failUnless('_rev' in doc3)

                # verifying access via dict api
                self.failUnless(doc1['_id'] in db)
                self.failUnless(doc2['_id'] in db)
                self.failUnless(doc3['_id'] in db)

                self.failUnless(db[doc1['_id']] == doc1)
                self.failUnless(db[doc2['_id']] == doc2)
                self.failUnless(db[doc3['_id']] == doc3)

                # test working context for updating docs
                with doc2 as working_doc:
                    working_doc['field1'] = [1,2,3]
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

