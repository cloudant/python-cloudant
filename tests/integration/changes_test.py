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
_changes_test_

changes module integration tests

"""

import logging
import sys
import unittest
import uuid

from cloudant import cloudant
from cloudant.credentials import read_dot_cloudant

def setup_logging():
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    log.addHandler(handler)
    return log

LOG = setup_logging()

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
            with cloudant(self.user, self.password, account=self.user) as c:
                c.delete_database(self.last_db)

    def test_changes(self):
        """
        _test_changes_

        Test to verify that we can connect to a live changes
        feed. Verify that we are actually staying connected by
        creating new docs while reading from the _changes feed.

        """
        dbname = "cloudant-changes-test-{0}".format(unicode(uuid.uuid4()))
        self.last_db = dbname

        with cloudant(self.user, self.password, account=self.user) as c:
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
                LOG.debug(unicode(change))
                if change is not None:
                    self.assertEqual(change['id'], doc['_id'])
                    n += 1
                    doc = make_doc(n)
                if n > 10:
                    break

            self.assertTrue(n > 10)

    def test_changes_include_docs(self):
        """
        _test_changes_include_docs

        Test to verify that we can pass 'include_docs' successfully
        through the changes pipeline.

        """
        dbname = "cloudant-changes-test-with-docs{0}".format(
            unicode(uuid.uuid4()))
        self.last_db = dbname

        with cloudant(self.user, self.password, account=self.user) as c:
            session = c.session()

            db = c.create_database(dbname)

            n = 0

            def make_doc(n):
                doc = db.create_document(
                    {"_id": "doc{}".format(n), "testing": "doc{}".format(n)}
                )
                return doc

            doc = make_doc(n)

            for change in db.changes(include_docs=True):
                LOG.debug(unicode(change))
                if change is not None:
                    self.assertEqual(change['id'], doc['_id'])
                    self.assertEqual(
                        # Verify that doc is included, and looks like
                        # the right doc.
                        change.get('doc', {}).get('testing', {}),
                        'doc{}'.format(n)
                    )
                    n += 1
                    doc = make_doc(n)
                if n > 10:
                    break

            self.assertTrue(n > 10)

if __name__ == '__main__':
    unittest.main()
