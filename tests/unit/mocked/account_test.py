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
_account_test_

account module unit tests

"""
import mock
import unittest
import requests

from cloudant.account import Cloudant, CouchDB
from cloudant.errors import CloudantException


class CouchDBAccountTests(unittest.TestCase):
    def setUp(self):
        """
        mock out requests.Session
        """
        self.patcher = mock.patch.object(requests, "Session")
        self.mock_session = self.patcher.start()
        self.mock_instance = mock.Mock()
        self.mock_instance.auth = None
        self.mock_instance.headers = {}
        self.mock_instance.cookies = {'AuthSession': 'COOKIE'}
        self.mock_instance.get = mock.Mock()
        self.mock_instance.post = mock.Mock()
        self.mock_instance.delete = mock.Mock()
        self.mock_instance.put = mock.Mock()
        self.mock_session.return_value = self.mock_instance
        self.username = "steve"
        self.password = "abc123"
        self.url = 'http://127.0.0.1:5984'

    def tearDown(self):
        self.patcher.stop()

    def test_db_updates(self):
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()
        updates_feed = """
            {"dbname": "somedb3", "type": "created", "account": "bob", "seq": "3-g1AAAABteJzLYWBgYMxgTmFQSElKzi9KdUhJMtHLTc1NzTcwMNdLzskvTUnMK9HLSy3JAapkSmTIY2H4DwRZGcyJzLlAIfa0tKQUQ2NTIkzIAgD_wSJc"}
            {"dbname": "somedb2", "type": "updated", "account": "bob", "seq": "4-g1AAAABteJzLYWBgYMxgTmFQSElKzi9KdUhJMtHLTc1NzTcwMNdLzskvTUnMK9HLSy3JAapkSmTIY2H4DwRZGcyJLLlAIfa0tKQUQ2NTIkzIAgAAASJd"}
            {"dbname": "somedb1", "type": "deleted", "account": "bob", "seq": "9-g1AAAABteJzLYWBgYMxgTmFQSElKzi9KdUhJMtHLTc1NzTcwMNdLzskvTUnMK9HLSy3JAapkSmTIY2H4DwRZGcyJnLlAIfa0tKQUQ2NTIkzIAgAA9iJi"}
            {"dbname": "somedb2", "type": "created", "account": "bob", "seq": "11-g1AAAABteJzLYWBgYMxgTmFQSElKzi9KdUhJMtHLTc1NzTcwMNdLzskvTUnMK9HLSy3JAapkSmTIY2H4DwRZGcyJ3LlAIfa0tKQUQ2NTIkzIAgABWCJk"}
            {"dbname": "somedb1", "type": "updated", "account": "bob", "seq": "12-g1AAAABteJzLYWBgYMxgTmFQSElKzi9KdUhJMtHLTc1NzTcwMNdLzskvTUnMK9HLSy3JAapkSmTIY2H4DwRZGcyJPLlAIfa0tKQUQ2NTIkzIAgABiSJl"}
        """
        with mock.patch('cloudant.account.Feed') as mock_feed:
            feed = (x.strip() for x in updates_feed.split('\n'))
            mock_feed.__iter__ = mock.MagicMock()
            mock_feed.return_value = feed

            updates = [u for u in c.db_updates()]

            self.assertEqual(len(updates), 5)

    def test_session_calls(self):
        """test session related methods"""
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()

        self.assertTrue(self.mock_session.called)

        self.assertEqual(
            self.mock_instance.auth,
            (self.username, self.password)
        )
        self.assertEqual(
            self.mock_instance.headers,
            {}
        )

        self.assertEqual('COOKIE', c.session_cookie())

        self.assertTrue(self.mock_instance.get.called)
        self.mock_instance.get.assert_has_calls(
            [ mock.call('http://127.0.0.1:5984/_session') ]
        )

        self.assertTrue(self.mock_instance.post.called)
        self.mock_instance.post.assert_has_calls(
            [ mock.call(
                  'http://127.0.0.1:5984/_session',
                  headers={'Content-Type': 'application/x-www-form-urlencoded'},
                  data={'password': 'abc123', 'name': 'steve'}
            ) ]
        )

        c.disconnect()
        self.assertTrue(self.mock_instance.delete.called)
        self.mock_instance.delete.assert_has_calls(
            [ mock.call('http://127.0.0.1:5984/_session') ]
        )

    def test_create_delete_methods(self):

        mock_resp = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {}
        mock_resp.text = "mock response"
        mock_resp.status_code = 201

        mock_del = mock.Mock()
        mock_del.status_code = 200

        mock_get = mock.Mock()
        mock_get.status_code = 404

        self.mock_instance.put.return_value = mock_resp
        self.mock_instance.delete.return_value = mock_del
        self.mock_instance.get.return_value = mock_get

        # instantiate and connect
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()
        self.assertTrue(self.mock_session.called)
        # create db call
        c.create_database("unittest")
        self.mock_instance.get.assert_has_calls(
            [ mock.call('http://127.0.0.1:5984/unittest') ]
        )
        self.mock_instance.put.assert_has_calls(
            [ mock.call('http://127.0.0.1:5984/unittest') ]
        )

        # delete db call
        mock_get.reset_mocks()
        mock_get.status_code = 200
        c.delete_database("unittest")
        self.mock_instance.get.assert_has_calls(
            [ mock.call('http://127.0.0.1:5984/unittest') ]
        )

        self.mock_instance.delete.assert_has_calls(
            [ mock.call('http://127.0.0.1:5984/unittest') ]
        )

        # create existing db fails
        mock_get.reset_mocks()
        mock_get.status_code = 200
        self.assertRaises(CloudantException, c.create_database, "unittest")

        # delete non-existing db fails
        mock_get.reset_mocks()
        mock_get.status_code = 404
        self.assertRaises(CloudantException, c.delete_database, "unittest")

    def test_basic_auth_str(self):
        c = CouchDB(self.username, self.password, url=self.url)
        auth_str = c.basic_auth_str()
        self.assertTrue(auth_str.startswith("Basic"))
        self.assertFalse(auth_str.endswith("Basic "))
        self.assertFalse(auth_str.endswith("Basic"))

    def test_all_dbs(self):
        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = ['db1', 'db2']
        self.mock_instance.get.return_value = mock_resp
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()
        self.assertEqual(c.all_dbs(), mock_resp.json.return_value)
        self.assertTrue(mock_resp.raise_for_status.called)

    def test_keys(self):
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()
        c.all_dbs = mock.Mock()
        c.all_dbs.return_value = ['db1', 'db2']
        self.assertListEqual(list(c.keys()), [])
        self.assertEqual(c.keys(remote=True), c.all_dbs.return_value)

    def test_getitem(self):
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()
        c['a'] = c._DATABASE_CLASS(c, 'a')
        c['b'] = c._DATABASE_CLASS(c, 'b')

        self.assertTrue(isinstance(c['a'], c._DATABASE_CLASS))
        self.assertTrue(isinstance(c['b'], c._DATABASE_CLASS))
        self.assertRaises(KeyError, c.__getitem__, 'd')

        with mock.patch('cloudant.account.CouchDatabase.exists') as mock_exists:
            mock_exists.return_value = True
            self.assertTrue(isinstance(c['c'], c._DATABASE_CLASS))

    def test_setitem(self):
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()
        self.assertRaises(CloudantException, c.__setitem__, 'c', 'womp')

        value = c._DATABASE_CLASS(c, 'a')
        c.__setitem__('c', value)
        self.assertTrue(c['c'] == value)

        value.exists = mock.Mock()
        value.exists.return_value = False
        value.create = mock.Mock()
        c.__setitem__('c', value, remote=True)
        self.assertTrue(value.create.called)
        self.assertTrue(c['c'] == value)

    def test_delitem(self):
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()
        c.delete_database = mock.Mock()

        c['a'] = c._DATABASE_CLASS(c, 'a')
        c['b'] = c._DATABASE_CLASS(c, 'b')

        del c['a']
        self.assertTrue('b' in c)
        self.assertTrue('a' not in c)

        c.__delitem__('b', remote=True)
        self.assertTrue(c.delete_database.called)

    def test_get(self):
        c = CouchDB(self.username, self.password, url=self.url)
        c.connect()

        c['a'] = c._DATABASE_CLASS(c, 'a')

        self.assertEqual(c.get('a'), c['a'])
        self.assertEqual(c.get('d', None), None)

        with mock.patch('cloudant.account.CouchDatabase.exists') as mock_exists:
            mock_exists.return_value = True
            self.assertTrue(isinstance(c.get('b', remote=True), c._DATABASE_CLASS))

        self.assertTrue(c.get('d', None, remote=True) is None)

class CloudantAccountTests(unittest.TestCase):
    """
    Unittests with mocked out remote calls

    """
    def setUp(self):
        """
        mock out requests.Session
        """
        self.patcher = mock.patch.object(requests, "Session")
        self.mock_session = self.patcher.start()
        self.mock_instance = mock.Mock()
        self.mock_instance.auth = None
        self.mock_instance.headers = {}
        self.mock_instance.cookies = {'AuthSession': 'COOKIE'}
        self.mock_instance.get = mock.Mock()
        self.mock_instance.post = mock.Mock()
        self.mock_instance.delete = mock.Mock()
        self.mock_instance.put = mock.Mock()
        self.mock_session.return_value = self.mock_instance
        self.username = "steve"
        self.password = "abc123"

    def tearDown(self):
        self.patcher.stop()

    def test_session_calls(self):
        """test session related methods"""
        c = Cloudant(
            self.username,
            self.password,
            url='https://steve.cloudant.com',
            x_cloudant_user=self.username
            )
        c.connect()

        self.assertTrue(self.mock_session.called)

        self.assertEqual(
            self.mock_instance.auth,
            (self.username, self.password)
        )

        self.assertEqual(
            self.mock_instance.headers['X-Cloudant-User'], 
            self.username
        )

        self.assertIsNotNone(self.mock_instance.headers['User-Agent'])

        self.assertEqual('COOKIE', c.session_cookie())

        self.assertTrue(self.mock_instance.get.called)
        self.mock_instance.get.assert_has_calls(
            [ mock.call('https://steve.cloudant.com/_session') ]
        )

        self.assertTrue(self.mock_instance.post.called)
        self.mock_instance.post.assert_has_calls(
            [ mock.call(
                  'https://steve.cloudant.com/_session',
                  headers={'Content-Type': 'application/x-www-form-urlencoded'},
                  data={'password': 'abc123', 'name': 'steve'}
            ) ]
        )

        c.disconnect()
        self.assertTrue(self.mock_instance.delete.called)
        self.mock_instance.delete.assert_has_calls(
            [ mock.call('https://steve.cloudant.com/_session') ]
        )

    def test_create_delete_methods(self):

        mock_resp = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {}
        mock_resp.text = "mock response"
        mock_resp.status_code = 201

        mock_del = mock.Mock()
        mock_del.status_code = 200

        mock_get = mock.Mock()
        mock_get.status_code = 404

        self.mock_instance.put.return_value = mock_resp
        self.mock_instance.delete.return_value = mock_del
        self.mock_instance.get.return_value = mock_get

        # instantiate and connect
        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()
        self.assertTrue(self.mock_session.called)
        # create db call
        c.create_database("unittest")
        self.mock_instance.get.assert_has_calls(
            [ mock.call('https://steve.cloudant.com/unittest') ]
        )
        self.mock_instance.put.assert_has_calls(
            [ mock.call('https://steve.cloudant.com/unittest') ]
        )

        # delete db call
        mock_get.reset_mocks()
        mock_get.status_code = 200
        c.delete_database("unittest")
        self.mock_instance.get.assert_has_calls(
            [ mock.call('https://steve.cloudant.com/unittest') ]
        )

        self.mock_instance.delete.assert_has_calls(
            [ mock.call('https://steve.cloudant.com/unittest') ]
        )

        # create existing db fails
        mock_get.reset_mocks()
        mock_get.status_code = 200
        self.assertRaises(CloudantException, c.create_database, "unittest")

        # delete non-existing db fails
        mock_get.reset_mocks()
        mock_get.status_code = 404
        self.assertRaises(CloudantException, c.delete_database, "unittest")

    def test_basic_auth_str(self):
        c = Cloudant(self.username, self.password, account=self.username)
        auth_str = c.basic_auth_str()
        self.assertTrue(auth_str.startswith("Basic"))
        self.assertFalse(auth_str.endswith("Basic "))
        self.assertFalse(auth_str.endswith("Basic"))

    def test_usage_endpoint(self):
        """test the usage endpoint method"""
        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {'usage': 'mock'}

        mock_get = mock.Mock()
        mock_get.return_value = mock_resp
        self.mock_instance.get = mock_get

        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()

        usage = c._usage_endpoint('endpoint', 2015, 12)
        self.assertEqual(usage, mock_resp.json.return_value)
        self.assertTrue(mock_resp.raise_for_status.called)

        mock_get.assert_has_calls( [ mock.call('endpoint/2015/12') ] )

        self.assertRaises(
            CloudantException,
            c._usage_endpoint, 'endpoint', month=12
        )

    def test_bill(self):
        """test bill API call"""
        with mock.patch(
            'cloudant.account.Cloudant._usage_endpoint'
        ) as mock_usage:
            mock_usage.return_value = {'usage': 'mock'}
            c = Cloudant(self.username, self.password, account=self.username)
            c.connect()
            bill = c.bill(2015, 12)
            self.assertEqual(bill, mock_usage.return_value)

    def test_volume_usage(self):
        with mock.patch(
            'cloudant.account.Cloudant._usage_endpoint'
        ) as mock_usage:
            mock_usage.return_value = {'usage': 'mock'}
            c = Cloudant(self.username, self.password, account=self.username)
            c.connect()
            bill = c.volume_usage(2015, 12)
            self.assertEqual(bill, mock_usage.return_value)

    def test_requests_usage(self):
        with mock.patch(
            'cloudant.account.Cloudant._usage_endpoint'
        ) as mock_usage:
            mock_usage.return_value = {'usage': 'mock'}
            c = Cloudant(self.username, self.password, account=self.username)
            c.connect()
            bill = c.requests_usage(2015, 12)
            self.assertEqual(bill, mock_usage.return_value)

    def test_shared_databases(self):
        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {'shared_databases': ['database1', 'database2']}
        self.mock_instance.get = mock.Mock()
        self.mock_instance.get.return_value = mock_resp

        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()

        shared = c.shared_databases()
        self.assertEqual(shared, ['database1', 'database2'])
        self.assertTrue(mock_resp.raise_for_status.called)

    def test_generate_api_key(self):
        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {'api': 'token'}
        self.mock_instance.post = mock.Mock()
        self.mock_instance.post.return_value = mock_resp

        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()

        api_key = c.generate_api_key()
        self.assertEqual(api_key, {'api': 'token'})
        self.assertTrue(mock_resp.raise_for_status.called)

    def test_cors_configuration(self):
        """test getting cors config"""
        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {'cors': 'blimey'}
        self.mock_instance.get = mock.Mock()
        self.mock_instance.get.return_value = mock_resp

        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()
        cors = c.cors_configuration()
        self.assertEqual(cors, mock_resp.json.return_value)
        self.assertTrue(mock_resp.raise_for_status.called)

    def test_cors_update(self):
        """test updating the cors config"""
        resp = {
            "enable_cors": True,
            "allow_credentials": True,
            "origins": [
                "https://example.com",
                "https://www.example.com"
            ]
        }

        mock_get = mock.Mock()
        mock_get.raise_for_status = mock.Mock()
        mock_get.json = mock.Mock()
        mock_get.json.return_value = {
            "enable_cors": True,
            "allow_credentials": True,
            "origins": [
                "https://example.com"
            ]
        }
        self.mock_instance.get = mock.Mock()
        self.mock_instance.get.return_value = mock_get

        mock_put = mock.Mock()
        mock_put.raise_for_status = mock.Mock()
        mock_put.json = mock.Mock()
        mock_put.json.return_value = resp
        self.mock_instance.put.return_value = mock_put

        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()
        cors = c.update_cors_configuration(
            enable_cors=True,
            allow_credentials=True,
            origins=[
                "https://www.example.com",
                "https://example.com"
            ]
        )

        self.assertEqual(cors, resp)
        self.assertTrue(self.mock_instance.get.called)
        self.assertTrue(self.mock_instance.put.called)

    def test_cors_update_origins_none(self):
        """test updating the cors config"""
        resp = {
            "enable_cors": True,
            "allow_credentials": True,
            "origins": []
        }

        mock_get = mock.Mock()
        mock_get.raise_for_status = mock.Mock()
        mock_get.json = mock.Mock()
        mock_get.json.return_value = {
            "enable_cors": True,
            "allow_credentials": True,
            "origins": ["https://example.com"]
        }
        self.mock_instance.get = mock.Mock()
        self.mock_instance.get.return_value = mock_get

        mock_put = mock.Mock()
        mock_put.raise_for_status = mock.Mock()
        mock_put.json = mock.Mock()
        mock_put.json.return_value = resp
        self.mock_instance.put.return_value = mock_put

        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()
        cors = c.update_cors_configuration(
            enable_cors=True,
            allow_credentials=True
        )

        self.assertEqual(cors, resp)
        self.assertTrue(self.mock_instance.get.called)
        self.assertTrue(self.mock_instance.put.called)

    def test_cors_origins_get(self):
        """test getting cors origins"""
        resp = {
            "enable_cors": True,
            "allow_credentials": True,
            "origins": [
                "https://example.com",
                "https://www.example.com"
            ]
        }

        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = resp
        self.mock_instance.get.return_value = mock_resp

        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()
        origins = c.cors_origins()

        self.assertEqual(origins, resp['origins'])
        self.assertTrue(self.mock_instance.get.called)

    def test_cors_disable(self):
        """test disabling cors"""
        resp = {
            "enable_cors": False,
            "allow_credentials": False,
            "origins": []
        }

        mock_put = mock.Mock()
        mock_put.raise_for_status = mock.Mock()
        mock_put.json = mock.Mock()
        mock_put.json.return_value = resp
        self.mock_instance.put.return_value = mock_put

        c = Cloudant(self.username, self.password, account=self.username)
        c.connect()
        cors = c.disable_cors()

        self.assertEqual(cors, resp)
        self.assertTrue(self.mock_instance.get.called)
        self.assertTrue(self.mock_instance.put.called)


if __name__ == '__main__':
    unittest.main()
