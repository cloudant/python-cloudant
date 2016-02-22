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
_document_test_

document module integration tests

"""

import requests
import unittest
import uuid

from cloudant import cloudant
from cloudant.credentials import read_dot_cloudant

from .. import unicode_

class DocumentTest(unittest.TestCase):
    """
    Verify that we can do stuff to a document.

    """

    def setUp(self):
        self.user, self.passwd = read_dot_cloudant(filename="~/.clou")
        self.dbname = unicode_("cloudant-document-tests-{0}".format(
            unicode_(uuid.uuid4())
        ))

    def tearDown(self):
        with cloudant(self.user, self.passwd, account=self.user) as c:
            c.delete_database(self.dbname)

    def test_delete(self):
        with cloudant(self.user, self.passwd, account=self.user) as c:
            db = c.create_database(self.dbname)

            doc1 = db.create_document({"_id": "doc1", "testing": "document 1"})

            doc1.save()
            doc1.fetch()

            doc1.delete()

            self.assertRaises(requests.HTTPError, doc1.fetch)

if __name__ == '__main__':
    unittest.main()

