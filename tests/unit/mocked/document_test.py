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
_document_test_

document module unit tests

"""
from __future__ import absolute_import

import mock
import requests
import unittest
import json

from cloudant.errors import CloudantException
from cloudant.document import Document

from ... import iteritems_


class DocumentTest(unittest.TestCase):

    def setUp(self):

        self.mock_session = mock.Mock()
        self.mock_session.get = mock.Mock()
        self.mock_session.post = mock.Mock()
        self.mock_session.put = mock.Mock()
        self.mock_session.delete = mock.Mock()

        self.account = mock.Mock()
        self.account.cloudant_url = "https://bob.cloudant.com"
        self.account.r_session = self.mock_session
        self.account.encoder = json.JSONEncoder
        self.database = mock.Mock()
        self.database.r_session = self.mock_session
        self.database.database_name = "unittest"
        self.database.cloudant_account = self.account

    def test_document_crud(self):
        """test basic crud operations with mocked backend"""
        doc = Document(self.database, "DUCKUMENT")
        # exists
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        self.mock_session.get.return_value = mock_resp
        self.assertTrue(doc.exists())
        self.assertTrue(self.mock_session.get.called)
        self.mock_session.get.assert_has_calls(
            [ mock.call('https://bob.cloudant.com/unittest/DUCKUMENT') ]
        )
        self.mock_session.get.reset_mock()

        # create
        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {'id': 'DUCKUMENT', 'rev': 'DUCK2'}
        self.mock_session.post.return_value = mock_resp

        doc.create()
        self.assertEqual(doc['_rev'], 'DUCK2')
        self.assertEqual(doc['_id'], 'DUCKUMENT')
        self.assertTrue(self.mock_session.post.called)
        self.mock_session.post.reset_mock()

        # fetch
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {
            '_id': 'DUCKUMENT', '_rev': 'DUCK2',
            'herp': 'HERP', 'derp': 'DERP'
        }
        self.mock_session.get.return_value = mock_resp
        doc.fetch()
        self.assertTrue('herp' in doc)
        self.assertTrue('derp' in doc)
        self.assertEqual(doc['herp'], 'HERP')
        self.assertEqual(doc['derp'], 'DERP')

        self.assertTrue(self.mock_session.get.called)
        self.mock_session.get.assert_has_calls(
            [ mock.call('https://bob.cloudant.com/unittest/DUCKUMENT') ]
        )
        self.mock_session.get.reset_mock()

        # save
        mock_put_resp = mock.Mock()
        mock_put_resp.status_code = 200
        mock_put_resp.raise_for_status = mock.Mock()
        mock_put_resp.json = mock.Mock()
        mock_put_resp.json.return_value = {'id': 'DUCKUMENT', 'rev': 'DUCK3'}
        self.mock_session.put.return_value = mock_put_resp
        mock_get_resp = mock.Mock()
        mock_get_resp.status_code = 200
        self.mock_session.get.return_value = mock_get_resp

        doc.save()
        self.assertEqual(doc['_rev'], 'DUCK3')
        self.assertEqual(doc['_id'], 'DUCKUMENT')
        self.assertTrue(self.mock_session.get.called)
        self.assertTrue(self.mock_session.put.called)

        self.mock_session.get.assert_has_calls(
            [ mock.call('https://bob.cloudant.com/unittest/DUCKUMENT') ]
        )
        self.mock_session.put.assert_has_calls(
            [ mock.call(
                  'https://bob.cloudant.com/unittest/DUCKUMENT',
                  headers={'Content-Type': 'application/json'},
                  data=mock.ANY
            ) ]
        )
        self.mock_session.get.reset_mock()
        self.mock_session.put.reset_mock()

        # delete
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = mock.Mock()
        self.mock_session.delete.return_value = mock_resp
        doc.delete()

        self.assertTrue(self.mock_session.delete.called)
        self.mock_session.delete.assert_has_calls(
            [ mock.call(
                  'https://bob.cloudant.com/unittest/DUCKUMENT',
                  params={'rev': 'DUCK3'}
            ) ]
        )
        self.mock_session.delete.reset_mock()
        # test delete with no rev explodes as expected
        self.assertRaises(CloudantException, doc.delete)

    def test_save_non_exists(self):
        """cover save case where doc doesnt exist"""
        mock_resp = mock.Mock()
        mock_resp.status_code = 404
        self.mock_session.get.return_value = mock_resp

        mock_post = mock.Mock()
        mock_post.raise_for_status = mock.Mock()
        mock_post.json = mock.Mock()
        mock_post.json.return_value = {'id': "created", "rev": "created"}
        mock_put = mock.Mock()
        mock_put.raise_for_status = mock.Mock()
        self.mock_session.post.return_value = mock_post
        self.mock_session.put.return_value = mock_put

        doc = Document(self.database, "DUCKUMENT")
        doc.save()

        self.assertEqual(doc['_id'], "created")
        self.assertEqual(doc['_rev'], "created")

    def test_document_edit_context(self):
        """test the editing context"""

        mock_fetch_resp = mock.Mock()
        mock_fetch_resp.status_code = 200
        mock_fetch_resp.raise_for_status = mock.Mock()
        mock_fetch_resp.json = mock.Mock()
        mock_fetch_resp.json.return_value = {
            'herp': 'HERP', 'derp': 'DERP'
        }
        self.mock_session.get.return_value = mock_fetch_resp

        mock_save_resp = mock.Mock()
        mock_save_resp.status_code = 200
        mock_save_resp.raise_for_status = mock.Mock()
        mock_save_resp.json = mock.Mock()
        mock_save_resp.json.return_value = {'id': "ID", "rev": "updated"}
        self.mock_session.put.return_value = mock_save_resp

        mock_encode = mock.Mock()
        mock_encode.encode = mock.Mock()

        doc = Document(self.database, "DUCKUMENT")
        doc._encoder = mock.Mock()
        doc._encoder.return_value = mock_encode

        with doc as d:
            d['new_field'] = "NARP"

        self.assertTrue(self.mock_session.get.called)
        self.assertTrue(self.mock_session.put.called)
        self.assertTrue(mock_encode.encode.called)
        payload = mock_encode.encode.call_args[0][0]

        for k, v in iteritems_(payload):
            self.assertTrue(k in doc)
            self.assertEqual(doc[k], v)

    def test_document_update_field(self):
        """
        _test_document_update_field_

        Tests for the field update functions.
        """

        # Setup a routine for testing conflict handing.
        errors = {'conflicts': 0}

        def raise_conflict(conflicts=3):
            if errors['conflicts'] < conflicts:
                errors['conflicts'] += 1
                err = requests.HTTPError()
                err.response = mock.Mock()
                err.response.status_code = 409
                raise err

        # Mock our our doc
        doc = Document(self.database, "HOWARD")

        mock_put_resp = mock.Mock()
        mock_put_resp.side_effect = mock.Mock()
        mock_put_resp.status_code = 200
        mock_put_resp.raise_for_status = raise_conflict
        mock_put_resp.json.side_effect = lambda: {'id': "ID", "rev": "updated"}
        self.mock_session.put.return_value = mock_put_resp
        mock_get_resp = mock.Mock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.side_effect = lambda: {"foo": "baz"}
        self.mock_session.get.return_value = mock_get_resp

        # Verify that our mock doc has the old value
        doc.fetch()
        self.assertEqual(doc["foo"], "baz")

        # And that we replace it with an updated value
        doc.update_field(doc.field_set, "foo", "bar")
        self.assertEqual(doc["foo"], "bar")

        # And verify that we called mock_session.put
        self.assertTrue(self.mock_session.put.called)

        # Try again, verifing that excessive conflicts get raised
        errors['conflicts'] = 0
        mock_put_resp.raise_for_status = lambda: raise_conflict(conflicts=11)

        self.assertRaises(
            requests.HTTPError,
            doc.update_field,
            doc.field_set,
            "foo",
            "bar"
        )

    def test_update_actions(self):
        """
        _test_update_actions_
        """

        doc = {
            "foo": "bar",
            "baz": [1, 2, 3, 4, 5]
        }

        c_doc = Document(self.database, "HOWARD")

        c_doc.list_field_append(doc, "baz", 10)
        c_doc.list_field_remove(doc, "baz", 3)
        c_doc.field_set(doc, "foo", "qux")

        self.assertTrue(10 in doc['baz'])
        self.assertFalse(3 in doc['baz'])
        self.assertEqual(doc['foo'], "qux")

    def test_attachment_put(self):
        """
        _test_attachment_put_
        """
        doc = Document(self.database, "DUCKUMENT")
        doc_id = 'DUCKUMENT'
        attachment = 'herpderp.txt'
        data = '/path/to/herpderp.txt'

        mock_get = mock.Mock()
        mock_get.raise_for_status = mock.Mock()
        mock_get.status_code = 200
        mock_get.json = mock.Mock()
        mock_get.json.return_value = {'_id': doc_id, '_rev': '1-abc'}
        self.mock_session.get.return_value = mock_get

        mock_put = mock.Mock()
        mock_put.raise_for_status = mock.Mock()
        mock_put.status_code = 201
        mock_put.json = mock.Mock()
        mock_put.json.return_value = {'id': doc_id, 'rev': '2-def', 'ok': True}
        self.mock_session.put.return_value = mock_put

        resp = doc.put_attachment(
            attachment,
            content_type='text/plain',
            data=data
        )

        self.assertEqual(resp['id'], doc_id)
        self.assertTrue(self.mock_session.get.called)
        self.assertTrue(self.mock_session.put.called)

    def test_attachment_get(self):
        """
        _test_attachment_get_
        """
        doc = Document(self.database, "DUCKUMENT")
        doc_id = 'DUCKUMENT'
        attachment = 'herpderp.txt'

        mock_get = mock.Mock()
        mock_get.raise_for_status = mock.Mock()
        mock_get.status_code = 200
        mock_get.json = mock.Mock()
        mock_get.json.return_value = {'_id': doc_id, '_rev': '1-abc'}

        mock_get_attch = mock.Mock()
        mock_get_attch.raise_for_status = mock.Mock()
        mock_get_attch.status_code = 200
        mock_get_attch.content = 'herp derp foo bar'

        self.mock_session.get.side_effect = [mock_get, mock_get_attch]

        resp = doc.get_attachment(attachment, attachment_type='binary')

        self.assertEqual(resp, mock_get_attch.content)
        self.assertEqual(self.mock_session.get.call_count, 2)

    def test_attachment_delete(self):
        """
        _test_attachment_delete_
        """
        doc = Document(self.database, "DUCKUMENT")
        doc_id = 'DUCKUMENT'
        attachment = 'herpderp.txt'

        mock_get = mock.Mock()
        mock_get.raise_for_status = mock.Mock()
        mock_get.status_code = 200
        mock_get.json = mock.Mock()
        mock_get.json.return_value = {'_id': doc_id, '_rev': '2-def'}
        self.mock_session.get.return_value = mock_get

        mock_del = mock.Mock()
        mock_del.raise_for_status = mock.Mock()
        mock_del.status_code = 200
        mock_del.json = mock.Mock()
        mock_del.json.return_value = {'id': doc_id, 'rev': '3-ghi', 'ok': True}
        self.mock_session.delete.return_value = mock_del

        resp = doc.delete_attachment(attachment)

        self.assertEqual(resp['id'], doc_id)
        self.assertTrue(self.mock_session.get.called)
        self.assertTrue(self.mock_session.delete.called)

if __name__ == '__main__':
    unittest.main()
