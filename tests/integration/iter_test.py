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
_iter_test_

Database iterator integration tests

"""

import unittest
import uuid

from cloudant import cloudant
from cloudant.credentials import read_dot_cloudant

from .. import _unicode


class IterTest(unittest.TestCase):
    """
    Verify that our database iterator works, and does the caching that
    we expect.

    """

    def setUp(self):
        self.user, self.password = read_dot_cloudant(filename="~/.clou")
        self.last_db = None

    def tearDown(self):
        if self.last_db is not None:
            with cloudant(self.user, self.password, account=self.user) as c:
                c.delete_database(self.last_db)

    def test_database_with_two_docs(self):
        """
        _test_database_with_two_docs_

        Test to make sure that our iterator works in the case where
        there are fewer docs to retrieve than it retrieves in one
        chunk.

        """
        dbname = "cloudant-itertest-twodocs-{0}".format(_unicode(uuid.uuid4()))
        self.last_db = dbname

        with cloudant(self.user, self.password, account=self.user) as c:
            session = c.session()

            db = c.create_database(dbname)

            doc1 = db.create_document(
                {"_id": "doc1", "testing": "doc1"}
            )
            doc2 = db.create_document(
                {"_id": "doc2", "testing": "doc2"}
            )
            docs = []

            # Make sure that iterator fetches docs
            for doc in db:
                docs.append(doc)

            self.assertEqual(len(docs), 2)

    def test_database_with_many_docs(self):
        """
        _test_database_with_many_docs_

        Test to make sure that we can iterator through stuff

        """
        dbname = "cloudant-itertest-manydocs-{0}".format(_unicode(uuid.uuid4()))
        self.last_db = dbname

        with cloudant(self.user, self.password, account=self.user) as c:
            session = c.session()

            db = c.create_database(dbname)

            for i in range(0,300):
                db.create_document({
                    "_id": "doc{0}".format(i),
                    "testing": "document {0}".format(i)
                })

            docs = []
            for doc in db:
                docs.append(doc)

            self.assertEqual(len(docs), 300)

            unique_ids = set([doc['id'] for doc in docs])
            self.assertEqual(len(unique_ids), 300)

if __name__ == '__main__':
    unittest.main()

