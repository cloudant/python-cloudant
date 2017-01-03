#!/usr/bin/env python
# Copyright (c) 2015, 2016 IBM. All rights reserved.
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
client module - Unit tests for CouchDB and Cloudant client classes

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import requests
import json
import base64
import sys
import os
import datetime

from cloudant import cloudant, couchdb, couchdb_admin_party
from cloudant.client import Cloudant, CouchDB
from cloudant.error import CloudantArgumentError, CloudantClientException
from cloudant.feed import Feed, InfiniteFeed
from cloudant._common_util import InfiniteSession

from .unit_t_db_base import UnitTestDbBase
from .. import bytes_, str_

class CloudantClientExceptionTests(unittest.TestCase):
    """
    Ensure CloudantClientException functions as expected.
    """

    def test_raise_without_code(self):
        """
        Ensure that a default exception/code is used if none is provided.
        """
        with self.assertRaises(CloudantClientException) as cm:
            raise CloudantClientException()
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_using_invalid_code(self):
        """
        Ensure that a default exception/code is used if invalid code is provided.
        """
        with self.assertRaises(CloudantClientException) as cm:
            raise CloudantClientException('foo')
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_without_args(self):
        """
        Ensure that a default exception/code is used if the message requested
        by the code provided requires an argument list and none is provided.
        """
        with self.assertRaises(CloudantClientException) as cm:
            raise CloudantClientException(404)
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_with_proper_code_and_args(self):
        """
        Ensure that the requested exception is raised.
        """
        with self.assertRaises(CloudantClientException) as cm:
            raise CloudantClientException(404, 'foo')
        self.assertEqual(cm.exception.status_code, 404)

class ClientTests(UnitTestDbBase):
    """
    CouchDB/Cloudant client unit tests
    """

    @unittest.skipIf(
        (os.environ.get('RUN_CLOUDANT_TESTS') is not None or
        (os.environ.get('ADMIN_PARTY') and os.environ.get('ADMIN_PARTY') == 'true')),
        'Skipping couchdb context manager test'
    )
    def test_couchdb_context_helper(self):
        """
        Test that the couchdb context helper works as expected.
        """
        try:
            with couchdb(self.user, self.pwd, url=self.url) as c:
                self.assertIsInstance(c, CouchDB)
                self.assertIsInstance(c.r_session, requests.Session)
        except Exception as err:
            self.fail('Exception {0} was raised.'.format(str(err)))

    @unittest.skipUnless(
        (os.environ.get('RUN_CLOUDANT_TESTS') is None and
        (os.environ.get('ADMIN_PARTY') and os.environ.get('ADMIN_PARTY') == 'true')),
        'Skipping couchdb_admin_party context manager test'
    )
    def test_couchdb_admin_party_context_helper(self):
        """
        Test that the couchdb_admin_party context helper works as expected.
        """
        try:
            with couchdb_admin_party(url=self.url) as c:
                self.assertIsInstance(c, CouchDB)
                self.assertIsInstance(c.r_session, requests.Session)
        except Exception as err:
            self.fail('Exception {0} was raised.'.format(str(err)))

    def test_constructor_with_url(self):
        """
        Test instantiating a client object using a URL
        """
        self.assertEqual(
            self.client.server_url,
            self.url
            )
        self.assertEqual(self.client.encoder, json.JSONEncoder)
        self.assertIsNone(self.client.r_session)

    def test_connect(self):
        """
        Test connect and disconnect functionality.
        """
        try:
            self.client.connect()
            self.assertIsInstance(self.client.r_session, requests.Session)
        finally:
            self.client.disconnect()
            self.assertIsNone(self.client.r_session)

    def test_auto_connect(self):
        """
        Test connect during client instantiation option.
        """
        try:
            self.set_up_client(auto_connect=True)
            self.assertIsInstance(self.client.r_session, requests.Session)
        finally:
            self.client.disconnect()
            self.assertIsNone(self.client.r_session)

    def test_multiple_connect(self):
        """
        Test that issuing a connect call to an already connected client does
        not cause any issue.
        """
        try:
            self.client.connect()
            self.set_up_client(auto_connect=True)
            self.client.connect()
            self.assertIsInstance(self.client.r_session, requests.Session)
        finally:
            self.client.disconnect()
            self.assertIsNone(self.client.r_session)

    def test_auto_renew_enabled(self):
        """
        Test that InfiniteSession is used when auto_renew is enabled.
        """
        try:
            self.set_up_client(auto_renew=True)
            self.client.connect()
            if os.environ.get('ADMIN_PARTY') == 'true':
                self.assertIsInstance(self.client.r_session, requests.Session)
            else:
                self.assertIsInstance(self.client.r_session, InfiniteSession)
        finally:
            self.client.disconnect()

    def test_auto_renew_enabled_with_auto_connect(self):
        """
        Test that InfiniteSession is used when auto_renew is enabled along with
        an auto_connect.
        """
        try:
            self.set_up_client(auto_connect=True, auto_renew=True)
            if os.environ.get('ADMIN_PARTY') == 'true':
                self.assertIsInstance(self.client.r_session, requests.Session)
            else:
                self.assertIsInstance(self.client.r_session, InfiniteSession)
        finally:
            self.client.disconnect()

    def test_session(self):
        """
        Test getting session information.  
        Session info is None if CouchDB Admin Party mode was selected.
        """
        try:
            self.client.connect()
            session = self.client.session()
            if self.client.admin_party:
                self.assertIsNone(session)
            else:
                self.assertEqual(session['userCtx']['name'], self.user)
        finally:
            self.client.disconnect()

    def test_session_cookie(self):
        """
        Test getting the session cookie.
        Session cookie is None if CouchDB Admin Party mode was selected.
        """
        try:
            self.client.connect()
            if self.client.admin_party:
                self.assertIsNone(self.client.session_cookie())
            else:
                self.assertIsNotNone(self.client.session_cookie())
        finally:
            self.client.disconnect()

    def test_basic_auth_str(self):
        """
        Test getting the basic authentication string.
        Basic auth string is None if CouchDB Admin Party mode was selected.
        """
        try:
            self.client.connect()
            if self.client.admin_party:
                self.assertIsNone(self.client.basic_auth_str())
            else:
                expected = 'Basic {0}'.format(
                    str_(base64.urlsafe_b64encode(bytes_("{0}:{1}".format(
                        self.user, self.pwd
                    ))))
                )
                self.assertEqual(self.client.basic_auth_str(), expected)
        finally:
            self.client.disconnect()

    def test_all_dbs(self):
        """
        Test getting a list of all of the databases
        """
        dbnames = [self.dbname() for _ in range(3)]
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
        self.client.connect()
        self.client.create_database(dbname)
        with self.assertRaises(CloudantClientException) as cm:
            self.client.create_database(dbname, throw_on_exists=True)
        self.assertEqual(cm.exception.status_code, 409)

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
        except CloudantClientException as err:
            self.assertEqual(str(err), 'Database no_such_db does not exist. '
                                       'Verify that the client is valid and try again.')
        finally:
            self.client.disconnect()

    def test_keys(self):
        """
        Test retrieving the list of database names
        """
        dbs = []
        try:
            self.client.connect()
            self.assertEqual(list(self.client.keys()), [])

            # create 10 new test dbs
            for _ in range(10):
                dbs.append(self.client.create_database(self.dbname()).database_name)

            self.assertTrue(set(dbs).issubset(set(self.client.keys(remote=True))))
            self.assertTrue(set(dbs).issubset(set(self.client.all_dbs())))

        finally:
            for db in dbs:
                self.client.delete_database(db)  # remove test db
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
        Test __delitem__ when removing a database
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
        Test retrieving a database
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
        except CloudantClientException as err:
            self.assertEqual(
                str(err),
                'Value must be set to a Database object. Found type: str')
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

    def test_db_updates_feed_call(self):
        """
        Test that db_updates() method call constructs and returns a Feed object
        """
        try:
            self.client.connect()
            db_updates = self.client.db_updates(limit=100)
            self.assertIs(type(db_updates), Feed)
            self.assertEqual(
                db_updates._url, '/'.join([self.client.server_url, '_db_updates']))
            self.assertIsInstance(db_updates._r_session, requests.Session)
            self.assertFalse(db_updates._raw_data)
            self.assertEqual(db_updates._options.get('limit'), 100)
        finally:
            self.client.disconnect()

@unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is not None,
    'Skipping Cloudant client specific tests'
)
class CloudantClientTests(UnitTestDbBase):
    """
    Cloudant specific client unit tests
    """

    def test_cloudant_context_helper(self):
        """
        Test that the cloudant context helper works as expected.
        """
        try:
            with cloudant(self.user, self.pwd, account=self.account) as c:
                self.assertIsInstance(c, Cloudant)
                self.assertIsInstance(c.r_session, requests.Session)
        except Exception as err:
            self.fail('Exception {0} was raised.'.format(str(err)))
    
    def test_constructor_with_account(self):
        """
        Test instantiating a client object using an account name
        """
        # Ensure that the client is new
        del self.client
        self.client = Cloudant(self.user, self.pwd, account=self.account)
        self.assertEqual(
            self.client.server_url,
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
            ua_parts = agent.split('/')
            self.assertEqual(len(ua_parts), 6)
            self.assertEqual(ua_parts[0], 'python-cloudant')
            self.assertEqual(ua_parts[1], sys.modules['cloudant'].__version__)
            self.assertEqual(ua_parts[2], 'Python')
            self.assertEqual(ua_parts[3], '{0}.{1}.{2}'.format(
                sys.version_info[0], sys.version_info[1], sys.version_info[2])),
            self.assertEqual(ua_parts[4], os.uname()[0]),
            self.assertEqual(ua_parts[5], os.uname()[4])
        finally:
            self.client.disconnect()

    def test_db_updates_infinite_feed_call(self):
        """
        Test that infinite_db_updates() method call constructs and returns an
        InfiniteFeed object
        """
        try:
            self.client.connect()
            db_updates = self.client.infinite_db_updates()
            self.assertIsInstance(db_updates, InfiniteFeed)
            self.assertEqual(
                db_updates._url, '/'.join([self.client.server_url, '_db_updates']))
            self.assertIsInstance(db_updates._r_session, requests.Session)
            self.assertFalse(db_updates._raw_data)
            self.assertDictEqual(db_updates._options, {'feed': 'continuous'})
        finally:
            self.client.disconnect()

    def test_billing_data(self):
        """
        Test the retrieval of billing data
        """
        try:
            self.client.connect()
            now = datetime.datetime.now()
            expected = [
                'data_volume',
                'total',
                'start',
                'end',
                'http_heavy',
                'http_light',
                'bill_type'
                ]
            # Test using year and month
            year = now.year
            month = now.month
            data = self.client.bill(year, month)
            self.assertTrue(all(x in expected for x in data.keys()))
            #Test without year and month arguments
            del data
            data = self.client.bill()
            self.assertTrue(all(x in expected for x in data.keys()))
        finally:
            self.client.disconnect()

    def test_set_year_without_month_for_billing_data(self):
        """
        Test raising an exception when retrieving billing data with only
        year parameter
        """
        try:
            self.client.connect()
            year = 2016
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.bill(year)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - 2016, month - None')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_month_without_year_for_billing_data(self):
        """
        Test raising an exception when retrieving billing data with only
        month parameter
        """
        try:
            self.client.connect()
            month = 1
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.bill(None, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - None, month - 1')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_invalid_type_year_for_billing_data(self):
        """
        Test raising an exception when retrieving billing data with a type
        string for the year parameter
        """
        try:
            self.client.connect()
            year = 'foo'
            month = 1
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.bill(year, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - foo, month - 1')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_year_with_invalid_month_for_billing_data(self):
        """
        Test raising an exception when retrieving billing data with an
        invalid month parameter
        """
        try:
            self.client.connect()
            year = 2016
            month = 13
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.bill(year, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - 2016, month - 13')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_volume_usage_data(self):
        """
        Test the retrieval of volume usage data
        """
        try:
            self.client.connect()
            now = datetime.datetime.now()
            expected = [
                'data_vol',
                'granularity',
                'start',
                'end'
                ]
            # Test using year and month
            year = now.year
            month = now.month
            data = self.client.volume_usage(year, month)
            self.assertTrue(all(x in expected for x in data.keys()))
            #Test without year and month arguments
            del data
            data = self.client.volume_usage()
            self.assertTrue(all(x in expected for x in data.keys()))
        finally:
            self.client.disconnect()

    def test_set_year_without_month_for_volume_usage_data(self):
        """
        Test raising an exception when retrieving volume usage data with only
        year parameter
        """
        try:
            self.client.connect()
            year = 2016
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.volume_usage(year)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - 2016, month - None')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_month_without_year_for_volume_usage_data(self):
        """
        Test raising an exception when retrieving volume usage data with only
        month parameter
        """
        try:
            self.client.connect()
            month = 1
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.volume_usage(None, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - None, month - 1')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_invalid_type_year_for_volume_usage_data(self):
        """
        Test raising an exception when retrieving volume usage data with a type
        string for the year parameter
        """
        try:
            self.client.connect()
            year = 'foo'
            month = 1
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.volume_usage(year, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - foo, month - 1')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_year_with_invalid_month_for_volume_usage_data(self):
        """
        Test raising an exception when retrieving volume usage data with an
        invalid month parameter
        """
        try:
            self.client.connect()
            year = 2016
            month = 13
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.volume_usage(year, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - 2016, month - 13')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_requests_usage_data(self):
        """
        Test the retrieval of requests usage data
        """
        try:
            self.client.connect()
            now = datetime.datetime.now()
            expected = [
                'requests',
                'granularity',
                'start',
                'end'
                ]
            # Test using year and month
            year = now.year
            month = now.month
            data = self.client.requests_usage(year, month)
            self.assertTrue(all(x in expected for x in data.keys()))
            #Test without year and month arguments
            del data
            data = self.client.requests_usage()
            self.assertTrue(all(x in expected for x in data.keys()))
        finally:
            self.client.disconnect()

    def test_set_year_without_month_for_requests_usage_data(self):
        """
        Test raising an exception when retrieving requests usage data with an
        invalid month parameter
        """
        try:
            self.client.connect()
            year = 2016
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.requests_usage(year)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - 2016, month - None')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_month_without_year_for_requests_usage_data(self):
        """
        Test raising an exception when retrieving requests usage data with only
        month parameter
        """
        try:
            self.client.connect()
            month = 1
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.requests_usage(None, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - None, month - 1')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_invalid_type_year_for_requests_usage_data(self):
        """
        Test raising an exception when retrieving requests usage data with
        a type string for the year parameter
        """
        try:
            self.client.connect()
            year = 'foo'
            month = 1
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.requests_usage(year, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - foo, month - 1')
            self.assertEqual(str(cm.exception), expected)
        finally:
            self.client.disconnect()

    def test_set_year_with_invalid_month_for_requests_usage_data(self):
        """
        Test raising an exception when retrieving requests usage data with only
        year parameter
        """
        try:
            self.client.connect()
            year = 2016
            month = 13
            with self.assertRaises(CloudantArgumentError) as cm:
                self.client.requests_usage(year, month)
            expected = ('Invalid year and/or month supplied.  '
                        'Found: year - 2016, month - 13')
            self.assertEqual(str(cm.exception), expected)
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
        Test the generation of an API key for this client account
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
        Test the retrieval of the current CORS configuration for this client
        account
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