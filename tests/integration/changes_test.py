"""
Test db changes feed
"""

import unittest
import uuid

from cloudant import cloudant
from cloudant.credentials import read_dot_cloudant

class ChangesTest(unittest.TestCase):
    """
    Verify that our database iterator works, and does the caching that
    we expect.

    """

    @classmethod
    def setUp(self):
        self.user, self.password = read_dot_cloudant(filename="~/.clou")
        self.last_db = None

    def tearDown(self):
        if self.last_db is not None:
            with cloudant(self.user, self.password) as c:
                c.delete_database(self.last_db)

    def test_changes(self):
        dbname = "cloudant-changes-test-{0}".format(unicode(uuid.uuid4()))
        self.last_db = dbname

        with cloudant(self.user, self.password) as c:
            session = c.session()

            db = c.create_database(dbname)

            n = 0

            def make_doc(n):
                doc = db.create_document(
                    {"_id": "doc{}".format(n), "testing": "doc{}".format(n)}
                )
                return doc

            doc = make_doc(n)

            for change in db.changes():
                if change is not None:
                    self.assertEqual(change['id'], doc['_id'])
                    n += 1
                    doc = make_doc(n)
                if n > 10:
                    break

            self.assertTrue(n > 10)
            
            
