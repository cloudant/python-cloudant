#!/usr/bin/env python
# Copyright (C) 2016, 2018 IBM Corp. All rights reserved.
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
Unit tests for the renewal of cookie auth

See configuration options for environment variables in unit_t_db_base
module docstring.
"""
import os
import time
import unittest

import requests
from cloudant._client_session import CookieSession
from nose.plugins.attrib import attr

from .unit_t_db_base import skip_if_not_cookie_auth, UnitTestDbBase


@attr(db=['cloudant','couch'])
@unittest.skipIf(os.environ.get('ADMIN_PARTY') == 'true', 'Skipping - Admin Party mode')
class AuthRenewalTests(UnitTestDbBase):
    """
    Auto renewal tests primarily testing the CookieSession functionality
    """

    def setUp(self):
        """
        Override UnitTestDbBase.setUp() with no set up
        """
        pass

    def tearDown(self):
        """
        Override UnitTestDbBase.tearDown() with no tear down
        """
        pass

    @skip_if_not_cookie_auth
    def test_client_db_doc_stack_success(self):
        """
        Ensure that auto renewal of cookie auth happens as expected and applies
        to all references of r_session throughout the library.
        """
        try:
            self.set_up_client(auto_connect=True, auto_renew=True)
            db = self.client._DATABASE_CLASS(self.client, self.dbname())
            db.create()
            db_2 = self.client._DATABASE_CLASS(self.client, self.dbname())
            doc = db.create_document({'_id': 'julia001', 'name': 'julia'})

            auth_session = self.client.r_session.cookies.get('AuthSession')
            db_auth_session = db.r_session.cookies.get('AuthSession')
            db_2_auth_session = db_2.r_session.cookies.get('AuthSession')
            doc_auth_session = doc.r_session.cookies.get('AuthSession')
            
            self.assertIsInstance(self.client.r_session, CookieSession)
            self.assertIsInstance(db.r_session, CookieSession)
            self.assertIsInstance(db_2.r_session, CookieSession)
            self.assertIsInstance(doc.r_session, CookieSession)
            self.assertIsNotNone(auth_session)
            self.assertTrue(
                auth_session ==
                db_auth_session ==
                db_2_auth_session ==
                doc_auth_session
            )
            self.assertTrue(db.exists())
            self.assertTrue(doc.exists())

            # Will cause a 401 response to be handled internally
            self.client.r_session.cookies.clear()
            self.assertIsNone(self.client.r_session.cookies.get('AuthSession'))
            self.assertIsNone(db.r_session.cookies.get('AuthSession'))
            self.assertIsNone(db_2.r_session.cookies.get('AuthSession'))
            self.assertIsNone(doc.r_session.cookies.get('AuthSession'))

            time.sleep(1) # Ensure a different cookie auth value

            # 401 response handled by renew of cookie auth and retry of request
            db_2.create()

            new_auth_session = self.client.r_session.cookies.get('AuthSession')
            new_db_auth_session = db.r_session.cookies.get('AuthSession')
            new_db_2_auth_session = db_2.r_session.cookies.get('AuthSession')
            new_doc_auth_session = doc.r_session.cookies.get('AuthSession')
            self.assertIsNotNone(new_auth_session)
            self.assertNotEqual(new_auth_session, auth_session)
            self.assertTrue(
                new_auth_session ==
                new_db_auth_session ==
                new_db_2_auth_session ==
                new_doc_auth_session
            )
            self.assertTrue(db.exists())
            self.assertTrue(doc.exists())
        finally:
            # Clean up
            self.client.delete_database(db.database_name)
            self.client.delete_database(db_2.database_name)
            self.client.disconnect()
            del self.client

    @skip_if_not_cookie_auth
    def test_client_db_doc_stack_failure(self):
        """
        Ensure that when the regular requests.Session is used that
        cookie auth renewal is not handled.
        """
        try:
            self.set_up_client(auto_connect=True)
            db = self.client._DATABASE_CLASS(self.client, self.dbname())
            db.create()
            
            self.assertIsInstance(self.client.r_session, requests.Session)
            self.assertIsInstance(db.r_session, requests.Session)

            # Will cause a 401 response
            self.client.r_session.cookies.clear()
            
            # 401 response expected to raised
            with self.assertRaises(requests.HTTPError) as cm:
                db.delete()
            self.assertEqual(cm.exception.response.status_code, 401)
        finally:
            # Manual reconnect
            self.client.disconnect()
            self.client.connect()
            # Clean up
            self.client.delete_database(db.database_name)
            self.client.disconnect()
            del self.client


if __name__ == '__main__':
    unittest.main()
