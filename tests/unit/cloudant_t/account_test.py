#!/usr/bin/env python
"""
_account_

Cloudant Account tests

"""
import mock
import unittest
import requests

from cloudant.account import Cloudant
from cloudant.errors import CloudantException


class AccountTests(unittest.TestCase):
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
        c = Cloudant(self.username, self.password)
        c.connect()

        self.failUnless(self.mock_session.called)

        self.assertEqual(
            self.mock_instance.auth,
            (self.username, self.password)
        )
        self.assertEqual(
            self.mock_instance.headers,
            {'X-Cloudant-User': self.username}
        )

        self.assertEqual('COOKIE', c.session_cookie())

        self.failUnless(self.mock_instance.get.called)
        self.mock_instance.get.assert_has_calls(
            mock.call('https://steve.cloudant.com/_session')
        )

        self.failUnless(self.mock_instance.post.called)
        self.mock_instance.post.assert_has_calls(
            mock.call(
                'https://steve.cloudant.com/_session',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={'password': 'abc123', 'name': 'steve'}
            )
        )

        c.disconnect()
        self.failUnless(self.mock_instance.delete.called)
        self.mock_instance.delete.assert_has_calls(
            mock.call('https://steve.cloudant.com/_session')
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
        c = Cloudant(self.username, self.password)
        c.connect()
        self.failUnless(self.mock_session.called)
        # create db call
        c.create_database("unittest")
        self.mock_instance.get.assert_has_calls(
            mock.call('https://steve.cloudant.com/unittest')
        )
        self.mock_instance.put.assert_has_calls(
            mock.call('https://steve.cloudant.com/unittest')
        )

        # delete db call
        mock_get.reset_mocks()
        mock_get.status_code = 200
        c.delete_database("unittest")
        self.mock_instance.get.assert_has_calls(
            mock.call('https://steve.cloudant.com/unittest')
        )

        self.mock_instance.delete.assert_has_calls(
            mock.call('https://steve.cloudant.com/unittest')
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
        c = Cloudant(self.username, self.password)
        auth_str = c.basic_auth_str()
        self.assertTrue(auth_str.startswith("Basic"))
        self.assertFalse(auth_str.endswith("Basic "))
        self.assertFalse(auth_str.endswith("Basic"))


if __name__ == '__main__':
    unittest.main()
