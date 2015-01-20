#!/usr/bin/env python
"""
_document_test_

Test class for CloudantDocument class

"""

import unittest
import mock

from cloudant.errors import CloudantException
from cloudant.database import CloudantDatabase
from cloudant.document import CloudantDocument


class CloudantDocumentTest(unittest.TestCase):

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
        doc = CloudantDocument(self.database, "DUCKUMENT")
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

        doc = CloudantDocument(self.database, "DUCKUMENT")
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


if __name__ == '__main__':
    unittest.main()
