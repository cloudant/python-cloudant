#!/usr/bin/env python
# Copyright (c) 2017 IBM. All rights reserved.
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
""" Unit tests for IAM authentication. """
import time
import unittest
import json
import mock

from cloudant._2to3 import Cookie
from cloudant.client import Cloudant
from cloudant.client_session import IAMSession

MOCK_API_KEY = 'CqbrIYzdO3btWV-5t4teJLY_etfT_dkccq-vO-5vCXSo'

MOCK_ACCESS_TOKEN = ('eyJraWQiOiIyMDE3MDQwMi0wMDowMDowMCIsImFsZyI6IlJTMjU2In0.e'
                     'yJpYW1faWQiOiJJQk1pZC0yNzAwMDdHRjBEIiwiaWQiOiJJQk1pZC0yNz'
                     'AwMDdHRjBEIiwicmVhbG1pZCI6IklCTWlkIiwiaWRlbnRpZmllciI6IjI'
                     '3MDAwN0dGMEQiLCJnaXZlbl9uYW1lIjoiVG9tIiwiZmFtaWx5X25hbWUi'
                     'OiJCbGVuY2giLCJuYW1lIjoiVG9tIEJsZW5jaCIsImVtYWlsIjoidGJsZ'
                     'W5jaEB1ay5pYm0uY29tIiwic3ViIjoidGJsZW5jaEB1ay5pYm0uY29tIi'
                     'wiYWNjb3VudCI6eyJic3MiOiI1ZTM1ZTZhMjlmYjJlZWNhNDAwYWU0YzN'
                     'lMWZhY2Y2MSJ9LCJpYXQiOjE1MDA0NjcxMDIsImV4cCI6MTUwMDQ3MDcw'
                     'MiwiaXNzIjoiaHR0cHM6Ly9pYW0ubmcuYmx1ZW1peC5uZXQvb2lkYy90b'
                     '2tlbiIsImdyYW50X3R5cGUiOiJ1cm46aWJtOnBhcmFtczpvYXV0aDpncm'
                     'FudC10eXBlOmFwaWtleSIsInNjb3BlIjoib3BlbmlkIiwiY2xpZW50X2l'
                     'kIjoiZGVmYXVsdCJ9.XAPdb5K4n2nYih-JWTWBGoKkxTXM31c1BB1g-Ci'
                     'auc2LxuoNXVTyz_mNqf1zQL07FUde1Cb_dwrbotjickNcxVPost6byQzt'
                     'fc0mRF1x2S6VR8tn7SGiRmXBjLofkTh1JQq-jutp2MS315XbTG6K6m16u'
                     'YzL9qfMnRvQHxsZWErzfPiJx-Trg_j7OX-qNFjdNUGnRpU7FmULy0r7Rx'
                     'Ld8mhG-M1yxVzRBAZzvM63s0XXfMnk1oLi-BuUUTqVOdrM0KyYMWfD0Q7'
                     '2PTo4Exa17V-R_73Nq8VPCwpOvZcwKRA2sPTVgTMzU34max8b5kpTzVGJ'
                     '6SXSItTVOUdAygZBng')

MOCK_OIDC_TOKEN_RESPONSE = {
    'access_token':  MOCK_ACCESS_TOKEN,
    'refresh_token': ('MO61FKNvVRWkSa4vmBZqYv_Jt1kkGMUc-XzTcNnR-GnIhVKXHUWxJVV3'
                      'RddE8Kqh3X_TZRmyK8UySIWKxoJ2t6obUSUalPm90SBpTdoXtaljpNyo'
                      'rmqCCYPROnk6JBym72ikSJqKHHEZVQkT0B5ggZCwPMnKagFj0ufs-VIh'
                      'CF97xhDxDKcIPMWG02xxPuESaSTJJug7e_dUDoak_ZXm9xxBmOTRKwOx'
                      'n5sTKthNyvVpEYPE7jIHeiRdVDOWhN5LomgCn3TqFCLpMErnqwgNYbyC'
                      'Bd9rNm-alYKDb6Jle4njuIBpXxQPb4euDwLd1osApaSME3nEarFWqRBz'
                      'hjoqCe1Kv564s_rY7qzD1nHGvKOdpSa0ZkMcfJ0LbXSQPs7gBTSVrBFZ'
                      'qwlg-2F-U3Cto62-9qRR_cEu_K9ZyVwL4jWgOlngKmxV6Ku4L5mHp4Kg'
                      'EJSnY_78_V2nm64E--i2ZA1FhiKwIVHDOivVNhggE9oabxg54vd63glp'
                      '4GfpNnmZsMOUYG9blJJpH4fDX4Ifjbw-iNBD7S2LRpP8b8vG9pb4WioG'
                      'zN43lE5CysveKYWrQEZpThznxXlw1snDu_A48JiL3Lrvo1LobLhF3zFV'
                      '-kQ='),
    'token_type': 'Bearer',
    'expires_in': 3600,  # 60mins
    'expiration': 1500470702  # Wed Jul 19 14:25:02 2017
}


class IAMAuthTests(unittest.TestCase):
    """ Unit tests for IAM authentication. """

    @staticmethod
    def _mock_cookie(expires_secs=300):
        return Cookie(
            version=0,
            name='IAMSession',
            value=('SQJCaUQxMqEfMEAyRKU6UopLVXceS0c9RPuQgDArCEYoN3l_TEY4gdf-DJ7'
                   '4sHfjcNEUVjfdOvA'),
            port=None,
            port_specified=False,
            domain='localhost',
            domain_specified=False,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=True,
            expires=int(time.time() + expires_secs),
            discard=False,
            comment=None,
            comment_url=None,
            rest={'HttpOnly': None},
            rfc2109=True)

    def test_iam_set_credentials(self):
        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984')
        self.assertEquals(iam._api_key, MOCK_API_KEY)

        new_api_key = 'some_new_api_key'
        iam.set_credentials(None, new_api_key)

        self.assertEquals(iam._api_key, new_api_key)

    @mock.patch('cloudant.client_session.ClientSession.request')
    def test_iam_get_access_token(self, m_req):
        m_response = mock.MagicMock()
        m_response.json.return_value = MOCK_OIDC_TOKEN_RESPONSE
        m_req.return_value = m_response

        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984')
        access_token = iam._get_access_token()

        m_req.assert_called_once_with(
            'POST',
            iam._token_url,
            auth=('bx', 'bx'),
            headers={'Accepts': 'application/json'},
            data={
                'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
                'response_type': 'cloud_iam',
                'apikey': MOCK_API_KEY
            }
        )

        self.assertEqual(access_token, MOCK_ACCESS_TOKEN)
        self.assertTrue(m_response.raise_for_status.called)
        self.assertTrue(m_response.json.called)

    @mock.patch('cloudant.client_session.ClientSession.request')
    @mock.patch('cloudant.client_session.IAMSession._get_access_token')
    def test_iam_login(self, m_token, m_req):
        m_token.return_value = MOCK_ACCESS_TOKEN
        m_response = mock.MagicMock()
        m_req.return_value = m_response

        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984')
        iam.login()

        m_req.assert_called_once_with(
            'POST',
            iam._session_url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps({'access_token': MOCK_ACCESS_TOKEN})
        )

        self.assertEqual(m_token.call_count, 1)
        self.assertTrue(m_response.raise_for_status.called)

    def test_iam_logout(self):
        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984')
        # add a valid cookie to jar
        iam.cookies.set_cookie(self._mock_cookie())
        self.assertEqual(len(iam.cookies.keys()), 1)
        iam.logout()
        self.assertEqual(len(iam.cookies.keys()), 0)

    @mock.patch('cloudant.client_session.ClientSession.get')
    def test_iam_get_session_info(self, m_get):
        m_info = {'ok': True, 'info': {'authentication_db': '_users'}}

        m_response = mock.MagicMock()
        m_response.json.return_value = m_info
        m_get.return_value = m_response

        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984')
        info = iam.info()

        m_get.assert_called_once_with(iam._session_url)

        self.assertEqual(info, m_info)
        self.assertTrue(m_response.raise_for_status.called)

    @mock.patch('cloudant.client_session.IAMSession.login')
    @mock.patch('cloudant.client_session.ClientSession.request')
    def test_iam_first_request(self, m_req, m_login):
        # mock 200
        m_response_ok = mock.MagicMock()
        type(m_response_ok).status_code = mock.PropertyMock(return_value=200)
        m_response_ok.json.return_value = {'ok': True}

        m_req.return_value = m_response_ok

        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984', auto_renew=True)
        iam.login()

        self.assertEqual(m_login.call_count, 1)
        self.assertEqual(m_req.call_count, 0)

        # add a valid cookie to jar
        iam.cookies.set_cookie(self._mock_cookie())

        resp = iam.request('GET', 'http://127.0.0.1:5984/mydb1')

        self.assertEqual(m_login.call_count, 1)
        self.assertEqual(m_req.call_count, 1)
        self.assertEqual(resp.status_code, 200)

    @mock.patch('cloudant.client_session.IAMSession.login')
    @mock.patch('cloudant.client_session.ClientSession.request')
    def test_iam_renew_cookie_on_expiry(self, m_req, m_login):
        # mock 200
        m_response_ok = mock.MagicMock()
        type(m_response_ok).status_code = mock.PropertyMock(return_value=200)
        m_response_ok.json.return_value = {'ok': True}

        m_req.return_value = m_response_ok

        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984', auto_renew=True)
        iam.login()

        # add an expired cookie to jar
        iam.cookies.set_cookie(self._mock_cookie(expires_secs=-300))

        resp = iam.request('GET', 'http://127.0.0.1:5984/mydb1')

        self.assertEqual(m_login.call_count, 2)
        self.assertEqual(m_req.call_count, 1)
        self.assertEqual(resp.status_code, 200)

    @mock.patch('cloudant.client_session.IAMSession.login')
    @mock.patch('cloudant.client_session.ClientSession.request')
    def test_iam_renew_cookie_on_401_success(self, m_req, m_login):
        # mock 200
        m_response_ok = mock.MagicMock()
        type(m_response_ok).status_code = mock.PropertyMock(return_value=200)
        m_response_ok.json.return_value = {'ok': True}
        # mock 401
        m_response_bad = mock.MagicMock()
        type(m_response_bad).status_code = mock.PropertyMock(return_value=401)

        m_req.side_effect = [m_response_bad, m_response_ok, m_response_ok]

        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984', auto_renew=True)
        iam.login()
        self.assertEqual(m_login.call_count, 1)

        # add a valid cookie to jar
        iam.cookies.set_cookie(self._mock_cookie())

        resp = iam.request('GET', 'http://127.0.0.1:5984/mydb1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(m_login.call_count, 2)
        self.assertEqual(m_req.call_count, 2)

        resp = iam.request('GET', 'http://127.0.0.1:5984/mydb1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(m_login.call_count, 2)
        self.assertEqual(m_req.call_count, 3)

    @mock.patch('cloudant.client_session.IAMSession.login')
    @mock.patch('cloudant.client_session.ClientSession.request')
    def test_iam_renew_cookie_on_401_failure(self, m_req, m_login):
        # mock 401
        m_response_bad = mock.MagicMock()
        type(m_response_bad).status_code = mock.PropertyMock(return_value=401)

        m_req.return_value = m_response_bad

        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984', auto_renew=True)
        iam.login()
        self.assertEqual(m_login.call_count, 1)

        # add a valid cookie to jar
        iam.cookies.set_cookie(self._mock_cookie())

        resp = iam.request('GET', 'http://127.0.0.1:5984/mydb1')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(m_login.call_count, 2)
        self.assertEqual(m_req.call_count, 2)

        resp = iam.request('GET', 'http://127.0.0.1:5984/mydb1')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(m_login.call_count, 3)
        self.assertEqual(m_req.call_count, 4)

    @mock.patch('cloudant.client_session.IAMSession.login')
    @mock.patch('cloudant.client_session.ClientSession.request')
    def test_iam_renew_cookie_disabled(self, m_req, m_login):
        # mock 401
        m_response_bad = mock.MagicMock()
        type(m_response_bad).status_code = mock.PropertyMock(return_value=401)

        m_req.return_value = m_response_bad

        iam = IAMSession(MOCK_API_KEY, 'http://127.0.0.1:5984', auto_renew=False)
        iam.login()
        self.assertEqual(m_login.call_count, 1)

        resp = iam.request('GET', 'http://127.0.0.1:5984/mydb1')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(m_login.call_count, 1)  # no attempt to renew
        self.assertEqual(m_req.call_count, 1)

        resp = iam.request('GET', 'http://127.0.0.1:5984/mydb1')
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(m_login.call_count, 1)  # no attempt to renew
        self.assertEqual(m_req.call_count, 2)

    @mock.patch('cloudant.client_session.IAMSession.login')
    @mock.patch('cloudant.client_session.ClientSession.request')
    def test_iam_client_create(self, m_req, m_login):
        # mock 200
        m_response_ok = mock.MagicMock()
        type(m_response_ok).status_code = mock.PropertyMock(return_value=200)
        m_response_ok.json.return_value = ['animaldb']

        m_req.return_value = m_response_ok

        # create IAM client
        client = Cloudant.iam('foo', MOCK_API_KEY)
        client.connect()

        # add a valid cookie to jar
        client.r_session.cookies.set_cookie(self._mock_cookie())

        dbs = client.all_dbs()

        self.assertEqual(m_login.call_count, 1)
        self.assertEqual(m_req.call_count, 1)
        self.assertEqual(dbs, ['animaldb'])

    @mock.patch('cloudant.client_session.IAMSession.login')
    @mock.patch('cloudant.client_session.IAMSession.set_credentials')
    def test_iam_client_session_login(self, m_set, m_login):
        # create IAM client
        client = Cloudant.iam('foo', MOCK_API_KEY)
        client.connect()

        # add a valid cookie to jar
        client.r_session.cookies.set_cookie(self._mock_cookie())

        client.session_login()

        m_set.assert_called_with(None, None)
        self.assertEqual(m_login.call_count, 2)
        self.assertEqual(m_set.call_count, 2)

    @mock.patch('cloudant.client_session.IAMSession.login')
    @mock.patch('cloudant.client_session.IAMSession.set_credentials')
    def test_iam_client_session_login_with_new_credentials(self, m_set, m_login):
        # create IAM client
        client = Cloudant.iam('foo', MOCK_API_KEY)
        client.connect()

        # add a valid cookie to jar
        client.r_session.cookies.set_cookie(self._mock_cookie())

        client.session_login('bar', 'baz')  # new creds

        m_set.assert_called_with('bar', 'baz')
        self.assertEqual(m_login.call_count, 2)
        self.assertEqual(m_set.call_count, 2)


if __name__ == '__main__':
    unittest.main()
