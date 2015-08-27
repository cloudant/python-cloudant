#!/usr/bin/env python
"""
_document_test_

Test class for Document class

"""

import mock
import requests
import unittest

from cloudant.errors import CloudantException
from cloudant.database import CloudantDatabase
from cloudant.document import Document


class DocumentTest(unittest.TestCase):

    def setUp(self):

        self.mock_session = mock.Mock()
        self.mock_session.get = mock.Mock()
        self.mock_session.post = mock.Mock()
        self.mock_session.put = mock.Mock()
        self.mock_session.delete = mock.Mock()

        self.account = mock.Mock()
        self.account._cloudant_url = "https://bob.cloudant.com"
        self.account._r_session = self.mock_session
        self.database = mock.Mock()
        self.database._r_session = self.mock_session
        self.database._database_name = "unittest"
        self.database._cloudant_account = self.account

    def test_document_crud(self):
        """test basic crud operations with mocked backend"""
        doc = Document(self.database, "DUCKUMENT")
        #exists
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        self.mock_session.get.return_value = mock_resp
        self.failUnless(doc.exists())
        self.failUnless(self.mock_session.get.called)
        self.mock_session.get.assert_has_calls(
            mock.call('https://bob.cloudant.com/unittest/DUCKUMENT')
        )
        self.mock_session.get.reset_mock()

        #create
        mock_resp = mock.Mock()
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {'id': 'DUCKUMENT', 'rev': 'DUCK2'}
        self.mock_session.post.return_value = mock_resp

        doc.create()
        self.assertEqual(doc['_rev'], 'DUCK2')
        self.assertEqual(doc['_id'], 'DUCKUMENT')
        self.failUnless(self.mock_session.post.called)
        self.mock_session.post.reset_mock()

        # fetch
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = mock.Mock()
        mock_resp.json = mock.Mock()
        mock_resp.json.return_value = {
            'herp': 'HERP', 'derp': 'DERP'
        }
        self.mock_session.get.return_value = mock_resp
        doc.fetch()
        self.failUnless('herp' in doc)
        self.failUnless('derp' in doc)
        self.assertEqual(doc['herp'], 'HERP')
        self.assertEqual(doc['derp'], 'DERP')

        self.failUnless(self.mock_session.get.called)
        self.mock_session.get.assert_has_calls(
            mock.call('https://bob.cloudant.com/unittest/DUCKUMENT')
        )
        self.mock_session.get.reset_mock()

        # save
        mock_put_resp = mock.Mock()
        mock_put_resp.status_code = 200
        mock_put_resp.raise_for_status = mock.Mock()
        self.mock_session.put.return_value = mock_put_resp
        mock_get_resp = mock.Mock()
        mock_get_resp.status_code = 200
        self.mock_session.get.return_value = mock_get_resp

        doc.save()
        self.failUnless(self.mock_session.get.called)
        self.failUnless(self.mock_session.put.called)

        self.mock_session.get.call.assert_has_call(
            mock.call('https://bob.cloudant.com/unittest/DUCKUMENT')
            )
        self.mock_session.put.assert_has_call(
            mock.call(
                'https://bob.cloudant.com/unittest/DUCKUMENT',
                headers={'Content-Type': 'application/json'},
                data=mock.ANY
                )
            )
        self.mock_session.get.reset_mock()
        self.mock_session.put.reset_mock()

        # delete
        mock_resp = mock.Mock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = mock.Mock()
        self.mock_session.delete.return_value = mock_resp
        doc.delete()

        self.failUnless(self.mock_session.delete.called)
        self.mock_session.delete.assert_has_call(
            mock.call(
                'https://bob.cloudant.com/unittest/DUCKUMENT',
                params={'rev': 'DUCK2'}
            )
        )
        self.mock_session.delete.reset_mock()
        # test delete with no rev explodes as expected
        del doc['_rev']
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
        self.mock_session.put.return_value = mock_save_resp

        mock_encode = mock.Mock()
        mock_encode.encode = mock.Mock()

        doc = Document(self.database, "DUCKUMENT")
        doc._encoder = mock.Mock()
        doc._encoder.return_value = mock_encode

        with doc as d:
            d['new_field'] = "NARP"

        self.failUnless(self.mock_session.get.called)
        self.failUnless(self.mock_session.put.called)
        self.failUnless(mock_encode.encode.called)
        payload = mock_encode.encode.call_args[0][0]

        for k, v in payload.iteritems():
            self.failUnless(k in doc)
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
        self.mock_session.put.return_value = mock_put_resp
        mock_get_resp = mock.Mock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.side_effect = lambda: {"foo": "baz"}
        self.mock_session.get.return_value = mock_get_resp

        # Verify that our mock doc has the old value
        doc.fetch()
        self.assertEqual(doc["foo"], "baz")

        # And that we replace it with an updated value
        doc.update_field(doc.field_replace, "foo", "bar")
        self.assertEqual(doc["foo"], "bar")

        # And verify that we called mock_session.put
        self.assertTrue(self.mock_session.put.called)

        # Try again, verifing that excessive conflicts get raised
        errors['conflicts'] = 0
        mock_put_resp.raise_for_status = lambda: raise_conflict(conflicts=11)

        self.assertRaises(
            requests.HTTPError,
            doc.update_field,
            doc.field_replace,
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

        c_doc.field_append(doc, "baz", 10)
        c_doc.field_remove(doc, "baz", 3)
        c_doc.field_replace(doc, "foo", "qux")

        self.assertTrue(10 in doc['baz'])
        self.assertFalse(3 in doc['baz'])
        self.assertEqual(doc['foo'], "qux")

if __name__ == '__main__':
    unittest.main()
