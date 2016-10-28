#!/usr/bin/env python
# Copyright (c) 2016 IBM. All rights reserved.
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
security_document module - Unit tests for the SecurityDocument class

See configuration options for environment variables in unit_t_db_base
module docstring.
"""

import unittest
import requests
import json
import os

from cloudant.security_document import SecurityDocument

from .unit_t_db_base import UnitTestDbBase


class SecurityDocumentTests(UnitTestDbBase):
    """
    SecurityDocument unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(SecurityDocumentTests, self).setUp()
        self.db_set_up()
        self.load_security_document_data()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(SecurityDocumentTests, self).tearDown()

    def test_constructor(self):
        """
        Test constructing a SecurityDocument
        """
        sdoc = SecurityDocument(self.db)
        self.assertIsInstance(sdoc, SecurityDocument)
        self.assertEqual(sdoc.r_session, self.db.r_session)

    def test_document_url(self):
        """
        Test that the document url is populated correctly
        """
        sdoc = SecurityDocument(self.db)
        self.assertEqual(
            sdoc.document_url,
            '/'.join([self.db.database_url, '_security'])
        )

    def test_json(self):
        """
        Test the security document dictionary renders as a JSON string
        """
        sdoc = SecurityDocument(self.db)
        sdoc.fetch()
        sdoc_as_json_string = sdoc.json()
        self.assertIsInstance(sdoc_as_json_string, str)
        sdoc_as_a_dict = json.loads(sdoc_as_json_string)
        self.assertDictEqual(sdoc_as_a_dict, sdoc)

    def test_fetch(self):
        """
        Test that the security document is retrieved as expected
        """
        sdoc = SecurityDocument(self.db)
        sdoc.fetch()
        self.assertDictEqual(sdoc, self.sdoc)

    def test_save(self):
        """
        Test that the security document is updated correctly
        """
        sdoc = SecurityDocument(self.db)
        sdoc.fetch()
        sdoc.update(self.mod_sdoc)
        sdoc.save()
        mod_sdoc = SecurityDocument(self.db)
        mod_sdoc.fetch()
        self.assertDictEqual(mod_sdoc, self.mod_sdoc)

    def test_context_manager(self):
        """
        Test that the context SecurityDocument context manager enter and exit
        routines work as expected.
        """
        with SecurityDocument(self.db) as sdoc:
            self.assertDictEqual(sdoc, self.sdoc)
            sdoc.update(self.mod_sdoc)
        mod_sdoc = SecurityDocument(self.db)
        mod_sdoc.fetch()
        self.assertDictEqual(mod_sdoc, self.mod_sdoc)
    

if __name__ == '__main__':
    unittest.main()
