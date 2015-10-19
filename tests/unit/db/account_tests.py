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
_account_tests_

account module - Unit tests for CouchDB and Cloudant account classes

The CouchDB tests are set to execute by default.

In order to run Cloudant tests the following environment variables
must be set:

- RUN_CLOUDANT_TESTS: Set this to anything to trigger Cloudant
  tests to run.
  example: export RUN_CLOUDANT_TESTS=1
- CLOUDANT_ACCOUNT: Set this to the Cloudant account that you wish
  to connect to.
  example: export CLOUDANT_ACCOUNT=account
- CLOUDANT_USER: Set this to the username to connect to the account
  with.
  example: export CLOUDANT_USER=user
- CLOUDANT_PASSWORD: Set this to the password for the username
  specified.
  example: export CLOUDANT_PASSWORD=password
- CLOUDANT_URL: Optionally set this to override the construction of
  Cloudant URL.
  example: export CLOUDANT_URL=https://account.cloudant.com

"""

import unittest
import requests
import json
import base64
import os
import uuid
from datetime import datetime

from cloudant.account import CouchDB, Cloudant
from cloudant.errors import CloudantException

class CouchDBAccountTests(unittest.TestCase):
    """
    CouchDB Class unit tests
    """

    @classmethod
    def setUpClass(self):
        """
        Set up CouchDB instance to be used by all tests

        If no user is specified then, assuming Admin Party and we
          need to create a user to run the CouchDB tests.
          
        Note: Admin Party is currently unsupported.
        """
        if os.environ.get('COUCHDB_URL') is None:
            os.environ['COUCHDB_URL'] = 'http://127.0.0.1:5984'

        if os.environ.get('COUCHDB_USER') is None:
            os.environ['COUCHDB_USER_CREATED'] = '1'
            os.environ['COUCHDB_USER'] = 'unit-test-user-{0}'.format(
                unicode(uuid.uuid4())
                )
            os.environ['COUCHDB_PASSWORD'] = 'unit-test-password'
            resp = requests.put(
                '{0}/_config/admins/{1}'.format(
                    os.environ['COUCHDB_URL'],
                    os.environ['COUCHDB_USER']
                    ),
                data='"{0}"'.format(os.environ['COUCHDB_PASSWORD'])
                )
            resp.raise_for_status()

    @classmethod
    def tearDownClass(self):
        """
        Clean up CouchDB instance once all tests are complete
        """
        if os.environ.get('COUCHDB_USER_CREATED') is not None:
            resp = requests.delete(
                '{0}://{1}:{2}@{3}/_config/admins/{4}'.format(
                    os.environ['COUCHDB_URL'].split('://', 1)[0],
                    os.environ['COUCHDB_USER'],
                    os.environ['COUCHDB_PASSWORD'],
                    os.environ['COUCHDB_URL'].split('://', 1)[1],
                    os.environ['COUCHDB_USER']
                    )
                )
            resp.raise_for_status()

    def setUp(self):
        """
        Set up test attributes for CouchDB Account tests
        """
        self.user = os.environ['COUCHDB_USER']
        self.pwd = os.environ['COUCHDB_PASSWORD']
        self.url = os.environ['COUCHDB_URL']
        self.client = CouchDB(self.user, self.pwd, url=self.url)

    def tearDown(self):
        """
        Ensure the client is new for each test
        """
        del self.client

    def dbname(self, database_name='account-unit-test-db'):
        return '{0}-{1}'.format(database_name, unicode(uuid.uuid4()))

    def test_constructor_with_url(self):
        """
        Test instantiating an account object using a URL
        """
        self.assertEqual(
            self.client.cloudant_url,
            self.url
            )
        self.assertEqual(self.client.encoder, json.JSONEncoder)
        self.assertIsNone(self.client.r_session)

    def test_connect(self):
        """
        Test connect and disconnect functionality
        """
        try:
            self.client.connect()
            self.assertIsInstance(self.client.r_session, requests.Session)
            self.assertEqual(self.client.r_session.auth, (self.user, self.pwd))
        finally:
            self.client.disconnect()
            self.assertIsNone(self.client.r_session)

    def test_session(self):
        """
        Test getting session information
        """
        try:
            self.client.connect()
            session = self.client.session()
            self.assertEqual(session['userCtx']['name'], self.user)
        finally:
            self.client.disconnect()

    def test_session_cookie(self):
        """
        Test getting the session cookie
        """
        try:
            self.client.connect()
            self.assertIsNotNone(self.client.session_cookie())
        finally:
            self.client.disconnect()

    def test_basic_auth_str(self):
        """
        Test getting the basic authentication string
        """
        try:
            self.client.connect()
            expected = 'Basic {0}'.format(
                base64.urlsafe_b64encode("{0}:{1}".format(self.user, self.pwd))
                )
            self.assertEqual(
                self.client.basic_auth_str(),
                expected
                )
        finally:
            self.client.disconnect()

    def test_all_dbs(self):
        """
        Test getting a list of all of the databases in the account
        """
        dbnames = []
        for _ in range(3):
            dbnames.append(self.dbname())
        try:
            self.client.connect()
            for dbname in dbnames:
                self.client.create_database(dbname)
            self.assertTrue(set(dbnames).issubset(self.client.all_dbs()))
        finally:
            for dbname in dbnames:
                self.client.delete_database(dbname)
            self.client.disconnect()

    def test_create_delete_database(self):
        """
        Test database creation and deletion
        """
        try:
            self.client.connect()
            dbname = self.dbname()
            # Create database
            db = self.client.create_database(dbname)
            self.assertTrue(db.exists())
            # Delete database
            self.assertIsNone(self.client.delete_database(dbname))
            self.assertFalse(db.exists())
        finally:
            self.client.disconnect()

    def test_create_existing_database(self):
        """
        Test creation of already existing database
        """
        dbname = self.dbname()
        try:
            self.client.connect()
            self.client.create_database(dbname)
            self.client.create_database(dbname, throw_on_exists=True)
            self.fail('Above statement should raise a CloudantException')
        except CloudantException, err:
            self.assertEqual(
                str(err),
                'Database {0} already exists'.format(dbname)
                )
        finally:
            self.client.delete_database(dbname)
            self.client.disconnect()

    def test_delete_non_existing_database(self):
        """
        Test deletion of non-existing database
        """
        try:
            self.client.connect()
            self.client.delete_database('no_such_db')
            self.fail('Above statement should raise a CloudantException')
        except CloudantException, err:
            self.assertEqual(str(err), 'Database no_such_db does not exist')
        finally:
            self.client.disconnect()

    def test_keys(self):
        """
        Test retrieving the list of database names for the given client account
        """
        try:
            self.client.connect()
            self.assertEqual(self.client.keys(), [])
            self.assertEqual(
                self.client.keys(remote=True),
                self.client.all_dbs()
                )
        finally:
            self.client.disconnect()

    def test_get_non_existing_db_via_getitem(self):
        """
        Test __getitem__ when retrieving a non-existing database
        """
        try:
            self.client.connect()
            db = self.client['no_such_db']
            self.fail('Above statement should raise a KeyError')
        except KeyError:
            pass
        finally:
            self.client.disconnect()

    def test_get_db_via_getitem(self):
        """
        Test __getitem__ when retrieving a database
        """
        dbname = self.dbname()
        try:
            self.client.connect()
            self.client.create_database(dbname)
            # Retrieve the database object from the server using __getitem__
            db = self.client[dbname]
            self.assertIsInstance(db, self.client._DATABASE_CLASS)
        finally:
            self.client.delete_database(dbname)
            self.client.disconnect()

    def test_delete_cached_db_object_via_delitem(self):
        """
        Test __delitem__ when removing a cached database object
        """
        dbname = self.dbname()
        try:
            self.client.connect()
            db = self.client.create_database(dbname)
            self.assertIsNotNone(self.client.get(dbname))
            del self.client[dbname]
            # Removed from local cache
            # Note: The get method returns a local db object by default
            self.assertIsNone(self.client.get(dbname))
            # Database still exists remotely
            # Note: __getitem__ returns the db object from the server
            self.assertEqual(self.client[dbname], db)
        finally:
            self.client.delete_database(dbname)
            self.client.disconnect()

    def test_delete_remote_db_via_delitem(self):
        """
        Test __delitem__ when removing a database from the account
        """
        dbname = self.dbname()
        try:
            self.client.connect()
            db = self.client.create_database(dbname)
            self.assertIsNotNone(self.client.get(dbname))
            self.client.__delitem__(dbname, remote=True)
            # Removed from local cache
            self.assertIsNone(self.client.get(dbname))
            # Database removed remotely as well
            try:
                db = self.client[dbname]
                self.fail('Above statement should raise a KeyError')
            except KeyError:
                pass
        finally:
            self.client.disconnect()

    def test_get_cached_db_object_via_get(self):
        """
        Test retrieving a database from the client database cache
        """
        dbname = self.dbname()
        try:
            self.client.connect()
            # Default returns None
            self.assertIsNone(self.client.get('no_such_db'))
            # Creates the database remotely and adds it to the 
            # client database cache
            db = self.client.create_database(dbname)
            # Locally cached database object is returned
            self.assertEqual(self.client.get(dbname), db)
        finally:
            self.client.delete_database(dbname)
            self.client.disconnect()

    def test_get_remote_db_via_get(self):
        """
        Test retrieving a database from the account
        """
        dbname = self.dbname()
        try:
            self.client.connect()
            # Default returns None
            self.assertIsNone(self.client.get('no_such_db', remote=True))
            # Creates the database remotely and ensure that
            # it is not in the client database local cache
            db = self.client.create_database(dbname)
            del self.client[dbname]
            self.assertIsNone(self.client.get(dbname))
            # Retrieve the database object from the server
            self.assertEqual(self.client.get(dbname, remote=True), db)
        finally:
            self.client.delete_database(dbname)
            self.client.disconnect()

    def test_set_non_db_value_via_setitem(self):
        """
        Test raising exception when value is not a database object
        """
        try:
            self.client.connect()
            self.client['not-a-db'] = 'This is not a database object'
            self.fail('Above statement should raise a CloudantException')
        except CloudantException, err:
            self.assertEqual(str(err), 'Value must be set to a Database object')
        finally:
            self.client.disconnect()

    def test_local_set_db_value_via_setitem(self):
        """
        Test setting a database object to the local database cache
        """
        try:
            self.client.connect()
            db = self.client._DATABASE_CLASS(self.client, 'local-not-on-server')
            # Value is set in the local database cache but not on the server
            self.client['local-not-on-server'] = db
            self.assertEqual(self.client.get('local-not-on-server'), db)
            self.assertFalse(db.exists())
        finally:
            self.client.disconnect()

    def test_create_db_via_setitem(self):
        """
        Test creating a database remotely using __setitem__
        """
        dbname = self.dbname()
        try:
            self.client.connect()
            db = self.client._DATABASE_CLASS(self.client, dbname)
            self.client.__setitem__(dbname, db, remote=True)
            self.assertTrue(db.exists())
        finally:
            self.client.delete_database(dbname)
            self.client.disconnect()

@unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is not None,
    'Skipping Cloudant Account tests'
    )
class CloudantAccountTests(CouchDBAccountTests):

    @classmethod
    def setUpClass(self):
        """
        For the Cloudant tests we expect an account to already be created.
        So we override the CouchDBAccountTests setUpClass and do nothing.
        """
        pass

    @classmethod
    def tearDownClass(self):
        """
        For the Cloudant tests we expect an account to already be created.
        So we override the CouchDBAccountTests tearDownClass and do nothing.
        """
        pass

    def setUp(self):
        """
        Set up test attributes for Cloudant Account tests
        """
        self.account = os.environ.get('CLOUDANT_ACCOUNT')
        self.user = os.environ.get('CLOUDANT_USER')
        self.pwd = os.environ.get('CLOUDANT_PASSWORD')
        self.url = os.environ.get(
            'CLOUDANT_URL',
            'https://{0}.cloudant.com'.format(self.account)
            )
        self.client = Cloudant(
            self.user,
            self.pwd,
            url=self.url,
            x_cloudant_user=self.account
            )
    
    def test_constructor_with_account(self):
        """
        Test instantiating an account object using an account name
        """
        # Ensure that the client is new
        del self.client
        self.client = Cloudant(self.user, self.pwd, account=self.account)
        self.assertEqual(
            self.client.cloudant_url,
            'https://{0}.cloudant.com'.format(self.account)
            )

    def test_connect_headers(self):
        """
        Test that the appropriate request headers are set
        """
        try:
            self.client.connect()
            self.assertEqual(
                self.client.r_session.headers['X-Cloudant-User'],
                self.account
                )
            agent = self.client.r_session.headers.get('User-Agent')
            self.assertTrue(agent.startswith('python-cloudant'))
        finally:
            self.client.disconnect()

    def test_billing_data(self):
        """
        Test the retrieval of billing data
        """
        try:
            self.client.connect()
            expected = [
                'data_volume',
                'total',
                'start',
                'end',
                'http_heavy',
                'http_light'
                ]
            # Test using year and month
            year = datetime.now().year
            month = datetime.now().month
            data = self.client.bill(year, month)
            self.assertTrue(all(x in expected for x in data.keys()))
            #Test without year and month arguments
            del data
            data = self.client.bill()
            self.assertTrue(all(x in expected for x in data.keys()))
        finally:
            self.client.disconnect()

    def test_volume_usage_data(self):
        """
        Test the retrieval of volume usage data
        """
        try:
            self.client.connect()
            expected = [
                'data_vol',
                'granularity',
                'start',
                'end'
                ]
            # Test using year and month
            year = datetime.now().year
            month = datetime.now().month
            data = self.client.volume_usage(year, month)
            self.assertTrue(all(x in expected for x in data.keys()))
            #Test without year and month arguments
            del data
            data = self.client.volume_usage()
            self.assertTrue(all(x in expected for x in data.keys()))
        finally:
            self.client.disconnect()

    def test_requests_usage_data(self):
        """
        Test the retrieval of requests usage data
        """
        try:
            self.client.connect()
            expected = [
                'requests',
                'granularity',
                'start',
                'end'
                ]
            # Test using year and month
            year = datetime.now().year
            month = datetime.now().month
            data = self.client.requests_usage(year, month)
            self.assertTrue(all(x in expected for x in data.keys()))
            #Test without year and month arguments
            del data
            data = self.client.requests_usage()
            self.assertTrue(all(x in expected for x in data.keys()))
        finally:
            self.client.disconnect()

    def test_shared_databases(self):
        """
        Test the retrieval of shared database list
        """
        try:
            self.client.connect()
            self.assertIsInstance(self.client.shared_databases(), list)
        finally:
            self.client.disconnect()

    def test_generate_api_key(self):
        """
        Test the generation of an API key for this account
        """
        try:
            self.client.connect()
            expected = ['key', 'password', 'ok']
            api_key = self.client.generate_api_key()
            self.assertTrue(all(x in expected for x in api_key.keys()))
            self.assertTrue(api_key['ok'])
        finally:
            self.client.disconnect()

    def test_cors_configuration(self):
        """
        Test the retrieval of the current CORS configuration for this account
        """
        try:
            self.client.connect()
            expected = ['allow_credentials', 'enable_cors', 'origins']
            cors = self.client.cors_configuration()
            self.assertTrue(all(x in expected for x in cors.keys()))
        finally:
            self.client.disconnect()

    def test_cors_origins(self):
        """
        Test the retrieval of the CORS origins list
        """
        try:
            self.client.connect()
            origins = self.client.cors_origins()
            self.assertIsInstance(origins, list)
        finally:
            self.client.disconnect()

    def test_disable_cors(self):
        """
        Test disabling CORS (assuming CORS is enabled)
        """
        try:
            self.client.connect()
            # Save original CORS settings
            save = self.client.cors_configuration()
            # Test CORS disable
            self.assertEqual(self.client.disable_cors(), {'ok': True})
            # Restore original CORS settings
            self.client.update_cors_configuration(
                save['enable_cors'],
                save['allow_credentials'],
                save['origins'],
                True
                )
        finally:
            self.client.disconnect()

    def test_update_cors_configuration(self):
        """
        Test updating CORS configuration
        """
        try:
            self.client.connect()
            # Save original CORS settings
            save = self.client.cors_configuration()
            # Test updating CORS settings, overwriting origins
            result = self.client.update_cors_configuration(
                True,
                True,
                ['https://ibm.com'],
                True)
            self.assertEqual(result, {'ok': True})
            updated_cors = self.client.cors_configuration()
            self.assertTrue(updated_cors['enable_cors'])
            self.assertTrue(updated_cors['allow_credentials'])
            expected = ['https://ibm.com']
            self.assertTrue(all(x in expected for x in updated_cors['origins']))
            # Test updating CORS settings, adding to origins
            result = self.client.update_cors_configuration(
                True,
                True,
                ['https://ibm.cloudant.com']
                )
            self.assertEqual(result, {'ok': True})
            del updated_cors
            updated_cors = self.client.cors_configuration()
            self.assertTrue(updated_cors['enable_cors'])
            self.assertTrue(updated_cors['allow_credentials'])
            expected.append('https://ibm.cloudant.com')
            self.assertTrue(all(x in expected for x in updated_cors['origins']))
            # Restore original CORS settings
            self.client.update_cors_configuration(
                save['enable_cors'],
                save['allow_credentials'],
                save['origins'],
                True
                )
        finally:
            self.client.disconnect()

if __name__ == '__main__':
    unittest.main()