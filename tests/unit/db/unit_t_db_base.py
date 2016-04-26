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
_unit_t_db_base_

unit_t_db_base module - The base class for all unit tests that target a db

The unit tests are set to execute by default against a CouchDB instance.

To run the tests using Admin Party security mode in Couchdb, set the 
ADMIN_PARTY environment variable to true.

  example: export ADMIN_PARTY=true

In order to run the unit tests against a Cloudant instance, set the
RUN_CLOUDANT_TESTS environment variable to something.

  example: export RUN_CLOUDANT_TESTS=1

Other valid environment variables:

CLOUDANT_ACCOUNT: Set this to the Cloudant account that you wish to connect to.
  - This is used for Cloudant tests only.
  
  example: export CLOUDANT_ACCOUNT=account

DB_USER: Set this to the username to connect with.  
  - Optional for CouchDB tests.  If omitted and ADMIN_PARTY is not "true" then
    a user will be created before tests are executed in CouchDB.
  - Mandatory for Cloudant tests.  

  example: export DB_USER=user

DB_PASSWORD: Set this to the password for the user specified.

  example: export DB_PASSWORD=password

DB_URL: Optionally set this to override the construction of the database URL.

  example: export DB_URL=https://account.cloudant.com

SKIP_DB_UPDATES: Set this to something to bypass all Cloudant _db_updates tests.

  example: export SKIP_DB_UPDATES=1

"""

import unittest
import requests
import os
import uuid

from cloudant.client import CouchDB, Cloudant
from cloudant.design_document import DesignDocument

from ... import unicode_

class UnitTestDbBase(unittest.TestCase):
    """
    The base class for all unit tests targeting a database
    """

    @classmethod
    def setUpClass(cls):
        """
        If targeting CouchDB, Set up a CouchDB instance otherwise do nothing.
          
        Note: Admin Party is currently unsupported so we must create a 
          CouchDB user for tests to function with a CouchDB instance if one is
          not provided.
        """
        if os.environ.get('RUN_CLOUDANT_TESTS') is None:
            if os.environ.get('DB_URL') is None:
                os.environ['DB_URL'] = 'http://127.0.0.1:5984'

            if (os.environ.get('ADMIN_PARTY') and
                os.environ.get('ADMIN_PARTY') == 'true'):
                if os.environ.get('DB_USER'):
                    del os.environ['DB_USER']
                if os.environ.get('DB_PASSWORD'):
                    del os.environ['DB_PASSWORD']
                return

            if os.environ.get('DB_USER') is None:
                os.environ['DB_USER_CREATED'] = '1'
                os.environ['DB_USER'] = 'user-{0}'.format(
                    unicode_(uuid.uuid4())
                    )
                os.environ['DB_PASSWORD'] = 'password'
                resp = requests.put(
                    '{0}/_config/admins/{1}'.format(
                        os.environ['DB_URL'],
                        os.environ['DB_USER']
                        ),
                    data='"{0}"'.format(os.environ['DB_PASSWORD'])
                    )
                resp.raise_for_status()

    @classmethod
    def tearDownClass(cls):
        """
        If necessary, clean up CouchDB instance once all tests are complete.
        """
        if (os.environ.get('RUN_CLOUDANT_TESTS') is None and
            os.environ.get('DB_USER_CREATED') is not None):
            resp = requests.delete(
                '{0}://{1}:{2}@{3}/_config/admins/{4}'.format(
                    os.environ['DB_URL'].split('://', 1)[0],
                    os.environ['DB_USER'],
                    os.environ['DB_PASSWORD'],
                    os.environ['DB_URL'].split('://', 1)[1],
                    os.environ['DB_USER']
                    )
                )
            del os.environ['DB_USER_CREATED']
            del os.environ['DB_USER']
            resp.raise_for_status()

    def setUp(self):
        """
        Set up test attributes for unit tests targeting a database
        """
        if os.environ.get('RUN_CLOUDANT_TESTS') is None:
            admin_party = False
            if (os.environ.get('ADMIN_PARTY') and
                os.environ.get('ADMIN_PARTY') == 'true'):
                admin_party = True
            self.user = os.environ.get('DB_USER', None)
            self.pwd = os.environ.get('DB_PASSWORD', None)
            self.url = os.environ['DB_URL']
            self.client = CouchDB(self.user, self.pwd, admin_party, url=self.url)
        else:
            self.account = os.environ.get('CLOUDANT_ACCOUNT')
            self.user = os.environ.get('DB_USER')
            self.pwd = os.environ.get('DB_PASSWORD')
            self.url = os.environ.get(
                'DB_URL',
                'https://{0}.cloudant.com'.format(self.account))
            self.client = Cloudant(
                self.user,
                self.pwd,
                url=self.url,
                x_cloudant_user=self.account)

    def tearDown(self):
        """
        Ensure the client is new for each test
        """
        del self.client

    def db_set_up(self):
        """
        Set up test attributes for Database tests
        """
        self.client.connect()
        self.test_dbname = self.dbname()
        self.db = self.client._DATABASE_CLASS(self.client, self.test_dbname)
        self.db.create()

    def db_tear_down(self):
        """
        Reset test attributes for each test
        """
        self.db.delete()
        self.client.disconnect()
        del self.test_dbname
        del self.db

    def dbname(self, database_name='db'):
        return '{0}-{1}'.format(database_name, unicode_(uuid.uuid4()))

    def populate_db_with_documents(self, doc_count=100, **kwargs):
        off_set = kwargs.get('off_set', 0)
        docs = [
            {'_id': 'julia{0:03d}'.format(i), 'name': 'julia', 'age': i}
            for i in range(off_set, off_set + doc_count)
        ]
        return self.db.bulk_docs(docs)

    def create_views(self):
        """
        Create a design document with views for use with tests.
        """
        self.ddoc = DesignDocument(self.db, 'ddoc001')
        self.ddoc.add_view(
            'view001',
            'function (doc) {\n emit(doc._id, 1);\n}'
        )
        self.ddoc.add_view(
            'view002',
            'function (doc) {\n emit(doc._id, 1);\n}',
            '_count'
        )
        self.ddoc.add_view(
            'view003',
            'function (doc) {\n emit(Math.floor(doc.age / 2), 1);\n}'
        )
        self.ddoc.add_view(
            'view004',
            'function (doc) {\n emit(Math.floor(doc.age / 2), 1);\n}',
            '_count'
        )
        self.ddoc.add_view(
            'view005',
            'function (doc) {\n emit([doc.name, doc.age], 1);\n}'
        )
        self.ddoc.add_view(
            'view006',
            'function (doc) {\n emit([doc.name, doc.age], 1);\n}',
            '_count'
        )
        self.ddoc.save()
        self.view001 = self.ddoc.get_view('view001')
        self.view002 = self.ddoc.get_view('view002')
        self.view003 = self.ddoc.get_view('view003')
        self.view004 = self.ddoc.get_view('view004')
        self.view005 = self.ddoc.get_view('view005')
        self.view006 = self.ddoc.get_view('view006')
