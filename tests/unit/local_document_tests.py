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
"""
local document module - Unit tests for the LocalDocument class

See configuration options for environment variables in unit_t_db_base
module docstring.
"""

import unittest
import mock
import json
import requests
import os

from cloudant.local_document import LocalDocument
from cloudant.error import CloudantLocalDocumentException

from .unit_t_db_base import UnitTestDbBase

class CloudantLocalDocumentExceptionTests(unittest.TestCase):
    """
    Ensure CloudantLocalDocumentException functions as expected.
    """

    def test_raise_without_code(self):
        """
        Ensure that a default exception/code is used if none is provided.
        """
        with self.assertRaises(CloudantLocalDocumentException) as cm:
            raise CloudantLocalDocumentException()
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_using_invalid_code(self):
        """
        Ensure that a default exception/code is used if invalid code is provided.
        """
        with self.assertRaises(CloudantLocalDocumentException) as cm:
            raise CloudantLocalDocumentException('foo')
        self.assertEqual(cm.exception.status_code, 100)


class LocalDocumentTests(UnitTestDbBase):
    """
    LocalDocument unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(LocalDocumentTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(LocalDocumentTests, self).tearDown()

    def test_constructor(self):
        """
        Test instantiating a LocalDocument
        """
        doc = LocalDocument(self.db, 'julia006')
        self.assertIsInstance(doc, LocalDocument)
        self.assertEqual(doc.r_session, self.db.r_session)
        self.assertEqual(doc.get('_id'), '_local/julia006')

    def test_constructor_local(self):
        """
        Test instantiating a LocalDocument with _local in the docid
        """
        doc = LocalDocument(self.db, 'julia006')
        self.assertIsInstance(doc, LocalDocument)
        self.assertEqual(doc.r_session, self.db.r_session)
        self.assertEqual(doc.get('_id'), '_local/julia006')

    def test_document_url(self):
        """
        Test that the document url is populated correctly
        """
        doc = LocalDocument(self.db, 'julia006')
        self.assertEqual(
            doc.document_url, '/'.join(
                [self.db.database_url, '_local', 'julia006']
            )
        )

    def test_document_url_encodes_correctly(self):
        """
        Test that the document url is populated and encoded correctly
        """
        doc = LocalDocument(self.db, 'http://example.com')
        self.assertEqual(
            doc.document_url, '/'.join(
                [self.db.database_url, '_local', 'http%3A%2F%2Fexample.com']
            )
        )
    
    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_exists(self):
        """
        Test if local document does not exists and if local document exists
        """
        doc = LocalDocument(self.db, 'julia006')
        self.assertFalse(doc.exists())
        self.db.r_session.put(
            doc.document_url,
            data=json.dumps({'_id': '_local/julia006'})
        )
        self.assertTrue(doc.exists())

    def test_exists_raises_error(self):
        """
        Test local document exists raises an HTTPError.
        """
        resp = requests.Response()
        resp.status_code = 400
        self.client.r_session.get = mock.Mock(return_value=resp)
        doc = LocalDocument(self.db, 'julia006')
        with self.assertRaises(requests.HTTPError) as cm:
            doc.exists()
        err = cm.exception
        self.assertEqual(err.response.status_code, 400)
        self.client.r_session.get.assert_called_with(doc.document_url)

    def test_json(self):
        """
        Test the local document dictionary renders as json appropriately
        """
        doc = LocalDocument(self.db, 'julia006')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc_as_json = doc.json()
        self.assertIsInstance(doc_as_json, str)
        self.assertEqual(json.loads(doc_as_json), doc)

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_create(self):
        """
        Test creating a local document and overwrites it if it already exists
        """
        doc = LocalDocument(self.db, 'julia006')
        exists = self.db.r_session.get(doc.document_url)
        self.assertEqual(exists.status_code, 404)
        self.assertFalse('_rev' in doc.keys())
        doc['name'] = 'julia'
        doc['age'] = 6
        doc.create()
        self.assertEqual(doc['_rev'], '0-1')
        new_doc = self.db.r_session.get(doc.document_url)
        new_doc_data = new_doc.json()
        self.assertEqual(
            new_doc.json(),
            {'_id': '_local/julia006', '_rev': '0-1', 'name': 'julia', 'age': 6}
        )
        doc['name'] = 'jules'
        doc.create()
        overwritten_doc = self.db.r_session.get(doc.document_url)
        overwritten_doc_data = new_doc.json()
        self.assertEqual(
            overwritten_doc.json(),
            {'_id': '_local/julia006', '_rev': '0-1', 'name': 'jules', 'age': 6}
        )

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_fetch_success(self):
        """
        Test fetching a local document
        """
        doc = LocalDocument(self.db, 'julia006')
        self.db.r_session.put(
            doc.document_url,
            data=json.dumps(
                {'_id': '_local/julia006', 'name': 'julia', 'age': 6}
            )
        )
        doc.fetch()
        self.assertEqual(
            doc,
            {'_id': '_local/julia006', '_rev': '0-1', 'name': 'julia', 'age': 6}
        )

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_fetch_not_found(self):
        """
        Test fetching a non-existing local document
        """
        doc = LocalDocument(self.db, 'julia006')
        with self.assertRaises(requests.HTTPError) as cm:
            doc.fetch()
        err = cm.exception
        self.assertEqual(err.response.status_code, 404)

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_save_reset_revision(self):
        """
        Test that a local document is overwritten and an explicitly set _rev is
        reset
        """
        doc = LocalDocument(self.db, 'julia006')
        self.db.r_session.put(
            doc.document_url,
            data=json.dumps(
                {'_id': '_local/julia006', '_rev': '0-6', 'name': 'julia', 'age': 6}
            )
        )
        doc.fetch()
        self.assertEqual(
            doc,
            {'_id': '_local/julia006', '_rev': '0-7', 'name': 'julia', 'age': 6}
        )
        doc.save(reset_revision=True)
        self.assertEqual(
            doc,
            {'_id': '_local/julia006', '_rev': '0-1', 'name': 'julia', 'age': 6}
        )

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_save_increment_revision(self):
        """
        Test that a local document is saved with an incremented revision number
        """
        doc = LocalDocument(self.db, 'julia006')
        self.db.r_session.put(
            doc.document_url,
            data=json.dumps(
                {'_id': '_local/julia006', '_rev': '0-6', 'name': 'julia', 'age': 6}
            )
        )
        doc.fetch()
        self.assertEqual(
            doc,
            {'_id': '_local/julia006', '_rev': '0-7', 'name': 'julia', 'age': 6}
        )
        del doc['_rev']
        doc.save()
        self.assertEqual(
            doc,
            {'_id': '_local/julia006', '_rev': '0-8', 'name': 'julia', 'age': 6}
        )

    def test_save_raises_error_on_get(self):
        """
        Test local document save raises an HTTPError on initial GET call.
        """
        resp = requests.Response()
        resp.status_code = 400
        self.client.r_session.get = mock.Mock(return_value=resp)
        doc = LocalDocument(self.db, 'julia006')
        with self.assertRaises(requests.HTTPError) as cm:
            doc.save()
        err = cm.exception
        self.assertEqual(err.response.status_code, 400)
        self.client.r_session.get.assert_called_with(doc.document_url)

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_save_raises_error_on_put(self):
        """
        Test local document save raises an HTTPError on PUT call.
        """
        resp = requests.Response()
        resp.status_code = 400
        self.client.r_session.put = mock.Mock(return_value=resp)
        doc = LocalDocument(self.db, 'julia006')
        with self.assertRaises(requests.HTTPError) as cm:
            doc.save()
        err = cm.exception
        self.assertEqual(err.response.status_code, 400)
        self.client.r_session.put.assert_called_with(
            doc.document_url,
            data='{"_id": "_local/julia006"}',
            headers={'Content-Type': 'application/json'}
        )

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_delete_success(self):
        """
        Test that a local document is deleted successfully
        """
        doc = LocalDocument(self.db, 'julia006')
        self.db.r_session.put(
            doc.document_url,
            data=json.dumps(
                {'_id': '_local/julia006', 'name': 'julia', 'age': 6}
            )
        )
        self.assertTrue(doc.exists())
        doc.delete()
        self.assertFalse(doc.exists())

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_delete_raises_error(self):
        """
        Test that a request to delete a local document raises an HTTPError when
        expected in the proper conditions
        """
        doc = LocalDocument(self.db, 'julia006')
        with self.assertRaises(requests.HTTPError) as cm:
            doc.delete()
        err = cm.exception
        self.assertEqual(err.response.status_code, 404)

    @unittest.skipUnless(
        os.environ.get('RUN_CLOUDANT_TESTS') is not None, 'Skipping Cloudant test'
    )
    def test_context_manager(self):
        """
        Test that the LocalDocument context manager fetches and saves
        upon entry and exit as expected
        """
        with LocalDocument(self.db, 'julia006') as doc:
            doc['name'] = 'julia'
            doc['age'] = 6

        resp = self.db.r_session.get(
            '/'.join([self.db.database_url, '_local', 'julia006'])
        )
        self.assertEqual(
            resp.json(),
            {'_id': '_local/julia006', '_rev': '0-1', 'name': 'julia', 'age': 6}
        )

        with LocalDocument(self.db, 'julia006') as doc:
            doc['name'] = 'jules'
            doc['age'] = 6

        resp = self.db.r_session.get(
            '/'.join([self.db.database_url, '_local', 'julia006'])
        )
        self.assertEqual(
            resp.json(),
            {'_id': '_local/julia006', '_rev': '0-2', 'name': 'jules', 'age': 6}
        )

    def test_context_manager_raises_error(self):
        """
        Test that the local context manager will raise an error if a problem
        occurs during initial fetch.
        """
        resp = requests.Response()
        resp.status_code = 400
        self.client.r_session.get = mock.Mock(return_value=resp)
        with self.assertRaises(requests.HTTPError) as cm:
            with LocalDocument(self.db, 'julia006') as doc:
                doc['name'] = 'does not matter'
                doc['age'] = 'who cares?'
        err = cm.exception
        self.assertEqual(err.response.status_code, 400)
        self.client.r_session.get.assert_called_with(
            '/'.join([self.db.database_url, '_local', 'julia006'])
        )


if __name__ == '__main__':
    unittest.main()
