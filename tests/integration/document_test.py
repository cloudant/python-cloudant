import posixpath
import requests
import time
import unittest
import uuid

from cloudant import cloudant
from cloudant.credentials import read_dot_cloudant

class DocumentTest(unittest.TestCase):
    """
    Verify that we can do stuff to a document.

    """

    def setUp(self):
        self.user, self.passwd = read_dot_cloudant(filename="~/.clou")
        self.dbname = u"cloudant-document-tests-{0}".format(
            unicode(uuid.uuid4())
        )

    def tearDown(self):
        with cloudant(self.user, self.passwd) as c:        
            c.delete_database(self.dbname)

    def test_delete(self):
        with cloudant(self.user, self.passwd) as c:
            db = c.create_database(self.dbname)

            doc1 = db.create_document({"_id": "doc1", "testing": "document 1"})

            doc1.save()
            doc1.fetch()

            doc1.delete()

            self.assertRaises(requests.HTTPError, doc1.fetch)
            
            
