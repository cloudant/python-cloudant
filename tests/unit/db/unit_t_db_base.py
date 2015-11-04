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

In order to run the unit tests against a Cloudant instance, set the
RUN_CLOUDANT_TESTS environment variable to something.

  example: export RUN_CLOUDANT_TESTS=1

Other valid environment variables:

CLOUDANT_ACCOUNT: Set this to the Cloudant account that you wish to connect to.
  - This is used for Cloudant tests only.
  
  example: export CLOUDANT_ACCOUNT=account

DB_USER: Set this to the username to connect with.  
  - Optional for CouchDB tests.  If omitted then a user will be created before
    tests are executed in CouchDB.
  - Mandatory for Cloudant tests.  

  example: export DB_USER=user

DB_PASSWORD: Set this to the password for the user specified.

  example: export CLOUDANT_PASSWORD=password

DB_URL: Optionally set this to override the construction of the database URL.

  example: export CLOUDANT_URL=https://account.cloudant.com

"""

import unittest
import requests
import os
import uuid

from cloudant.account import CouchDB, Cloudant

class UnitTestDbBase(unittest.TestCase):
    """
    The base class for all unit tests targeting a database
    """

    @classmethod
    def setUpClass(self):
        """
        If targeting CouchDB, Set up a CouchDB instance otherwise do nothing.
          
        Note: Admin Party is currently unsupported so we must create a 
          CouchDB user for tests to function with a CouchDB instance if one is
          not provided.
        """
        if os.environ.get('RUN_CLOUDANT_TESTS') is None:
            if os.environ.get('DB_URL') is None:
                os.environ['DB_URL'] = 'http://127.0.0.1:5984'

            if os.environ.get('DB_USER') is None:
                os.environ['DB_USER_CREATED'] = '1'
                os.environ['DB_USER'] = 'unit-test-user-{0}'.format(
                    unicode(uuid.uuid4())
                    )
                os.environ['DB_PASSWORD'] = 'unit-test-password'
                resp = requests.put(
                    '{0}/_config/admins/{1}'.format(
                        os.environ['DB_URL'],
                        os.environ['DB_USER']
                        ),
                    data='"{0}"'.format(os.environ['DB_PASSWORD'])
                    )
                resp.raise_for_status()

    @classmethod
    def tearDownClass(self):
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
        	self.user = os.environ['DB_USER']
        	self.pwd = os.environ['DB_PASSWORD']
        	self.url = os.environ['DB_URL']
        	self.client = CouchDB(self.user, self.pwd, url=self.url)
        else:
        	self.account = os.environ.get('CLOUDANT_ACCOUNT')
        	self.user = os.environ.get('DB_USER')
        	self.pwd = os.environ.get('DB_PASSWORD')
        	self.url = os.environ.get(
        		'DB_URL',
        		'https://{0}.cloudant.com'.format(self.account)
        		)
        	self.client = Cloudant(
        		self.user,
        		self.pwd,
        		url=self.url,
        		x_cloudant_user=self.account
        		)

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

    def dbname(self, database_name='unit-test-db'):
        return '{0}-{1}'.format(database_name, unicode(uuid.uuid4()))

    def populate_db_with_documents(self, doc_count=100):
        docs = [
            {'_id': 'julia{0:03d}'.format(i), 'name': 'julia', 'age': i}
            for i in xrange(doc_count)
        ]
        return self.db.bulk_docs(docs)
