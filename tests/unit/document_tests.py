#!/usr/bin/env python
# Copyright (C) 2015, 2018 IBM Corp. All rights reserved.
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
_document_tests_

document module - Unit tests for the Document class

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import mock
import json
import requests
import os
import uuid
import inspect

from cloudant.document import Document
from cloudant.error import CloudantDocumentException

from .. import StringIO, unicode_
from .unit_t_db_base import UnitTestDbBase

def find_fixture(name):
    import tests.unit.fixtures as fixtures
    dirname = os.path.dirname(inspect.getsourcefile(fixtures))
    filename = os.path.join(dirname, name)
    return filename

class CloudantDocumentExceptionTests(unittest.TestCase):
    """
    Ensure CloudantDocumentException functions as expected.
    """

    def test_raise_without_code(self):
        """
        Ensure that a default exception/code is used if none is provided.
        """
        with self.assertRaises(CloudantDocumentException) as cm:
            raise CloudantDocumentException()
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_using_invalid_code(self):
        """
        Ensure that a default exception/code is used if invalid code is provided.
        """
        with self.assertRaises(CloudantDocumentException) as cm:
            raise CloudantDocumentException('foo')
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_without_args(self):
        """
        Ensure that a default exception/code is used if the message requested
        by the code provided requires an argument list and none is provided.
        """
        with self.assertRaises(CloudantDocumentException) as cm:
            raise CloudantDocumentException(102)
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_with_proper_code_and_args(self):
        """
        Ensure that the requested exception is raised.
        """
        with self.assertRaises(CloudantDocumentException) as cm:
            raise CloudantDocumentException(102, 'foo')
        self.assertEqual(cm.exception.status_code, 102)

class DocumentTests(UnitTestDbBase):
    """
    Document unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(DocumentTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(DocumentTests, self).tearDown()

    def test_constructor_with_docid(self):
        """
        Test instantiating a Document providing an id
        """
        doc = Document(self.db, 'julia006')
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.r_session, self.db.r_session)
        self.assertEqual(doc.get('_id'), 'julia006')

    def test_document_url(self):
        """
        Test that the document url is populated correctly
        """
        doc = Document(self.db, 'julia006')
        self.assertEqual(
            doc.document_url, '/'.join((self.db.database_url, 'julia006'))
        )

    def test_document_url_encodes_correctly(self):
        """
        Test that the document url is populated and encoded correctly
        """
        doc = Document(self.db, 'http://example.com')
        self.assertEqual(
            doc.document_url,
            '/'.join((self.db.database_url, 'http%3A%2F%2Fexample.com'))
        )

    def test_design_document_url(self):
        """
        Test that the document url is populated correctly when a design document
        id is provided.
        """
        doc = Document(self.db, '_design/ddoc001')
        self.assertEqual(
            doc.document_url,
            '/'.join((self.db.database_url, '_design/ddoc001'))
        )

    def test_design_document_url_encodes_correctly(self):
        """
        Test that the document url is populated and encoded correctly
        """
        doc = Document(self.db, '_design/http://example.com')
        self.assertEqual(
            doc.document_url,
            '/'.join((self.db.database_url, '_design/http%3A%2F%2Fexample.com'))
        )

    def test_constructor_without_docid(self):
        """
        Test instantiating a Document without providing an id
        """
        doc = Document(self.db)
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.r_session, self.db.r_session)
        self.assertIsNone(doc.get('_id'))
        self.assertIsNone(doc.document_url)

    def test_document_exists(self):
        """
        Tests that the result of True is expected when the document exists,
        and False is expected when the document is nonexistent remotely.
        """
        doc = Document(self.db)
        self.assertFalse(doc.exists())
        doc['_id'] = 'julia006'
        self.assertFalse(doc.exists())
        doc.create()
        self.assertTrue(doc.exists())

    def test_document_exists_raises_httperror(self):
        """
        Test document exists raises an HTTPError.
        """
        # Mock HTTPError when running against CouchDB and Cloudant
        resp = requests.Response()
        resp.status_code = 400
        self.client.r_session.head = mock.Mock(return_value=resp)
        doc = Document(self.db)
        doc['_id'] = 'julia006'
        with self.assertRaises(requests.HTTPError) as cm:
            doc.exists()
        err = cm.exception
        self.assertEqual(err.response.status_code, 400)
        self.client.r_session.head.assert_called_with(doc.document_url)

    def test_retrieve_document_json(self):
        """
        Test the document dictionary renders as json appropriately
        """
        doc = Document(self.db)
        doc['_id'] = 'julia006'
        doc['name'] = 'julia'
        doc['age'] = 6
        doc_as_json = doc.json()
        self.assertIsInstance(doc_as_json, str)
        self.assertEqual(json.loads(doc_as_json), doc)

    def test_create_document_with_docid(self):
        """
        Test creating a document providing an id
        """
        doc = Document(self.db, 'julia006')
        doc['name'] = 'julia'
        doc['age'] = 6
        self.assertFalse(doc.exists())
        self.assertIsNone(doc.get('_rev'))
        doc.create()
        self.assertTrue(doc.exists())
        self.assertTrue(doc.get('_rev').startswith('1-'))

    def test_create_document_with_docid_encoded_url(self):
        """
        Test creating a document providing an id that has an encoded url
        """
        doc = Document(self.db, 'http://example.com')
        doc['name'] = 'julia'
        doc['age'] = 6
        self.assertFalse(doc.exists())
        self.assertIsNone(doc.get('_rev'))
        doc.create()
        self.assertTrue(doc.exists())
        self.assertTrue(doc.get('_rev').startswith('1-'))

    def test_create_document_without_docid(self):
        """
        Test creating a document remotely without providing an id
        """
        doc = Document(self.db)
        doc['name'] = 'julia'
        doc['age'] = 6
        self.assertFalse(doc.exists())
        self.assertIsNone(doc.get('_id'))
        self.assertIsNone(doc.get('_rev'))
        doc.create()
        self.assertTrue(doc.exists())
        self.assertIsNotNone(doc.get('_id'))
        self.assertTrue(doc.get('_rev').startswith('1-'))

    def test_create_existing_document(self):
        """
        Test creating an already existing document
        """
        doc = Document(self.db, 'julia006')
        doc.create()
        with self.assertRaises(requests.HTTPError) as cm:
            doc.create()
        err = cm.exception
        self.assertEqual(
            err.response.status_code,
            409
        )

    def test_fetch_document_without_docid(self):
        """
        Test fetching document content with no id provided
        """
        doc = Document(self.db)
        try:
            doc.fetch()
            self.fail('Above statement should raise an Exception')
        except CloudantDocumentException as err:
            self.assertEqual(
                str(err),
                'A document id is required to fetch document contents. '
                'Add an _id key and value to the document and re-try.'
            )

    def test_fetch_non_existing_document(self):
        """
        Test fetching document content from a non-existing document
        """
        doc = Document(self.db, 'julia006')
        try:
            doc.fetch()
            self.fail('Above statement should raise an Exception')
        except requests.HTTPError as err:
            self.assertEqual(err.response.status_code, 404)

    def test_fetch_existing_document_with_docid(self):
        """
        Test fetching document content from an existing document
        """
        doc = Document(self.db, 'julia006')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc.create()
        new_doc = Document(self.db, 'julia006')
        new_doc.fetch()
        self.assertEqual(new_doc, doc)

    def test_appended_error_message_using_save_with_invalid_key(self):
        """
        Test that saving a document with an invalid remote key will
        throw an HTTPError with additional error details from util
        method append_response_error_content.
        """
        # First create the document
        doc = Document(self.db, 'julia006')
        # Add an invalid key and try to save document
        doc['_invalid_key'] = 'jules'
        with self.assertRaises(requests.HTTPError) as cm:
            doc.save()
        err = cm.exception
        # Should be a 400 error code, but CouchDB 1.6 issues a 500
        if err.response.status_code == 500:
            # Check this is CouchDB 1.x
            self.assertTrue(self.client.r_session.head(self.url).headers['Server'].find('CouchDB/1.') >= 0,
                            '500 returned but was not CouchDB 1.x')
            self.assertEqual(
                str(err.response.reason),
                'Internal Server Error doc_validation Bad special document member: _invalid_key'
            )
        else:
            self.assertEqual(
                str(err.response.reason),
                'Bad Request doc_validation Bad special document member: _invalid_key'
            )
            self.assertEqual(
                err.response.status_code,
                400
            )

    def test_fetch_existing_document_with_docid_encoded_url(self):
        """
        Test fetching document content from an existing document where the
        document id requires an encoded url
        """
        doc = Document(self.db, 'http://example.com')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc.create()
        new_doc = Document(self.db, 'http://example.com')
        new_doc.fetch()
        self.assertEqual(new_doc, doc)

    def test_create_document_using_save(self):
        """
        Test that save functionality works.  If a document does
        not exist remotely then create it.
        """
        doc = Document(self.db, 'julia006')
        doc['name'] = 'julia'
        doc['age'] = 6
        self.assertIsNone(doc.get('_rev'))
        doc.save()
        self.assertTrue(doc.exists())
        self.assertTrue(doc['_rev'].startswith('1-'))
        remote_doc = Document(self.db, 'julia006')
        remote_doc.fetch()
        self.assertEqual(remote_doc, doc)

    def test_update_document_using_save(self):
        """
        Test that save functionality works.  If a document exists
        remotely then update it.
        """
        # First create the document
        doc = Document(self.db, 'julia006')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc.save()
        # Now test that the document gets updated
        doc['name'] = 'jules'
        doc.save()
        self.assertTrue(doc['_rev'].startswith('2-'))
        remote_doc = Document(self.db, 'julia006')
        remote_doc.fetch()
        self.assertEqual(remote_doc, doc)
        self.assertEqual(remote_doc['name'], 'jules')

    def test_update_document_with_encoded_url(self):
        """
        Test that updating a document where the document id requires that the
        document url be encoded is successful.
        """
        # First create the document
        doc = Document(self.db, 'http://example.com')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc.save()
        # Now test that the document gets updated
        doc['name'] = 'jules'
        doc.save()
        self.assertTrue(doc['_rev'].startswith('2-'))
        remote_doc = Document(self.db, 'http://example.com')
        remote_doc.fetch()
        self.assertEqual(remote_doc, doc)
        self.assertEqual(remote_doc['name'], 'jules')

    def test_list_field_append_successfully(self):
        """
        Test the static helper method to successfully append to a list field.
        """
        doc = Document(self.db)
        self.assertEqual(doc, {})
        doc.list_field_append(doc, 'pets', 'cat')
        self.assertEqual(doc, {'pets': ['cat']})
        doc.list_field_append(doc, 'pets', 'dog')
        self.assertEqual(doc, {'pets': ['cat', 'dog']})
        doc.list_field_append(doc, 'pets', None)
        self.assertEqual(doc, {'pets': ['cat', 'dog']})

    def test_list_field_append_failure(self):
        """
        Test the static helper method to append to a list
        field errors as expected.
        """
        doc = Document(self.db)
        doc.field_set(doc, 'name', 'julia')
        try:
            doc.list_field_append(doc, 'name', 'isabel')
            self.fail('Above statement should raise an Exception')
        except CloudantDocumentException as err:
            self.assertEqual(str(err), 'The field name is not a list.')
        self.assertEqual(doc, {'name': 'julia'})

    def test_list_field_remove_successfully(self):
        """
        Test the static helper method to successfully remove from a list field.
        """
        doc = Document(self.db)
        self.assertEqual(doc, {})
        doc.list_field_append(doc, 'pets', 'cat')
        doc.list_field_append(doc, 'pets', 'dog')
        self.assertEqual(doc, {'pets': ['cat', 'dog']})
        doc.list_field_remove(doc, 'pets', 'dog')
        self.assertEqual(doc, {'pets': ['cat']})

    def test_list_field_remove_failure(self):
        """
        Test the static helper method to remove from a list
        field errors as expected.
        """
        doc = Document(self.db)
        doc.field_set(doc, 'name', 'julia')
        try:
            doc.list_field_remove(doc, 'name', 'julia')
            self.fail('Above statement should raise an Exception')
        except CloudantDocumentException as err:
            self.assertEqual(str(err), 'The field name is not a list.')
        self.assertEqual(doc, {'name': 'julia'})

    def test_field_set_and_replace(self):
        """
        Test the static helper method to set or replace a field value.
        """
        doc = Document(self.db)
        self.assertEqual(doc, {})
        doc.field_set(doc, 'name', 'julia')
        self.assertEqual(doc, {'name': 'julia'})
        doc.field_set(doc, 'name', 'jules')
        self.assertEqual(doc, {'name': 'jules'})
        doc.field_set(doc, 'pets', ['cat', 'dog'])
        self.assertEqual(doc, {'name': 'jules', 'pets': ['cat', 'dog']})
        doc.field_set(doc, 'pets', None)
        self.assertEqual(doc, {'name': 'jules'})

    def test_update_field(self):
        """
        Test that we can update a single field remotely using the
        update_field method.
        """
        doc = Document(self.db, 'julia006')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc['pets'] = ['cat', 'dog']
        doc.create()
        self.assertTrue(doc['_rev'].startswith('1-'))
        self.assertEqual(doc['pets'], ['cat', 'dog'])
        doc.update_field(doc.list_field_append, 'pets', 'fish')
        self.assertTrue(doc['_rev'].startswith('2-'))
        self.assertEqual(doc['pets'], ['cat', 'dog', 'fish'])

    def test_delete_document_failure(self):
        """
        Test failure condition when attempting to remove a document
        from the remote database.
        """
        doc = Document(self.db, 'julia006')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc['pets'] = ['cat', 'dog']
        try:
            doc.delete()
            self.fail('Above statement should raise an Exception')
        except CloudantDocumentException as err:
            self.assertEqual(
                str(err), 
                'Attempting to delete a doc with no _rev. '
                'Try running .fetch and re-try.'
            )

    def test_delete_document_success(self):
        """
        Test that we can remove a document from the remote
        database successfully.
        """
        doc = Document(self.db, 'julia006')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc['pets'] = ['cat', 'dog']
        doc.create()
        self.assertTrue(doc.exists())
        doc.delete()
        self.assertFalse(doc.exists())
        self.assertEqual(doc, {'_id': 'julia006'})

    def test_delete_document_success_with_encoded_url(self):
        """
        Test that we can remove a document from the remote
        database successfully when the document id requires an encoded url.
        """
        doc = Document(self.db, 'http://example.com')
        doc['name'] = 'julia'
        doc['age'] = 6
        doc['pets'] = ['cat', 'dog']
        doc.create()
        self.assertTrue(doc.exists())
        doc.delete()
        self.assertFalse(doc.exists())
        self.assertEqual(doc, {'_id': 'http://example.com'})

    def test_document_context_manager(self):
        """
        Test that the __enter__ and __exit__ methods perform as expected
        when initiated through a document context manager.
        """
        new_doc = Document(self.db, 'julia006')
        new_doc.create()
        self.assertTrue(new_doc.exists())
        del new_doc
        with Document(self.db, 'julia006') as doc:
            self.assertTrue(all(x in list(doc.keys()) for x in ['_id', '_rev']))
            self.assertTrue(doc['_rev'].startswith('1-'))
            doc['name'] = 'julia'
            doc['age'] = 6
        self.assertTrue(doc['_rev'].startswith('2-'))
        self.assertEqual(self.db['julia006'], doc)

    def test_document_context_manager_no_doc_id(self):
        """
        Test that the __enter__ and __exit__ methods perform as expected
        with no document id when initiated through a document context manager
        """
        with Document(self.db) as doc:
            doc['_id'] = 'julia006'
            doc['name'] = 'julia'
            doc['age'] = 6
        self.assertTrue(doc['_rev'].startswith('1-'))
        self.assertEqual(self.db['julia006'], doc)

    def test_document_context_manager_doc_create(self):
        """
        Test that the document context manager will create a doc if it does
        not yet exist.
        """
        with Document(self.db, 'julia006') as doc:
            doc['name'] = 'julia'
            doc['age'] = 6
        self.assertTrue(doc['_rev'].startswith('1-'))
        self.assertEqual(self.db['julia006'], doc)

    def test_setting_id(self):
        """
        Ensure that proper processing occurs when setting the _id
        """
        doc = Document(self.db)
        self.assertIsNone(doc.get('_id'))
        self.assertEqual(doc._document_id, None)
        doc['_id'] = 'julia006'
        self.assertEqual(doc['_id'], 'julia006')
        self.assertEqual(doc._document_id, 'julia006')

    def test_removing_id(self):
        """
        Ensure that proper processing occurs when removing the _id
        """
        doc = Document(self.db)
        doc['_id'] = 'julia006'
        del doc['_id']
        self.assertIsNone(doc.get('_id'))
        self.assertEqual(doc._document_id, None)

    def test_get_text_attachment(self):
        """
        Test the retrieval of a text attachment
        """
        doc = self.db.create_document(
            {'_id': 'julia006', 'name': 'julia', 'age': 6}
        )
        attachment = StringIO()
        try:
            filename = 'attachment-{0}{1}'.format(unicode_(uuid.uuid4()), '.txt')
            attachment.write('This is line one of the attachment.\n')
            attachment.write('This is line two of the attachment.\n')
            resp = doc.put_attachment(
                filename,
                'text/plain',
                attachment.getvalue()
            )
            with open(find_fixture(filename), 'wt') as f:
                text_attachment = doc.get_attachment(filename, write_to=f)
                self.assertEqual(text_attachment, attachment.getvalue())
            with open(find_fixture(filename), 'rt') as f:
                self.assertEqual(f.read(), attachment.getvalue())
        finally:
            attachment.close()
            os.remove(find_fixture(filename))

    def test_get_json_attachment(self):
        """
        Test the retrieval of a json attachment
        """
        doc = self.db.create_document(
            {'_id': 'julia006', 'name': 'julia', 'age': 6}
        )
        try:
            filename = 'attachment-{0}{1}'.format(unicode_(uuid.uuid4()), '.json')
            data = {'foo': 'bar', 'baz': 99}
            resp = doc.put_attachment(
                filename,
                'application/json',
                json.dumps(data)
            )
            with open(find_fixture(filename), 'wt') as f:
                json_attachment = doc.get_attachment(filename, write_to=f)
                self.assertIsInstance(json_attachment, dict)
                self.assertEqual(json_attachment, data)
            with open(find_fixture(filename), 'rt') as f:
                self.assertEqual(f.read(), json.dumps(data))
        finally:
            os.remove(find_fixture(filename))

    def test_get_binary_attachment(self):
        """
        Test the retrieval of a binary attachment
        """
        doc = self.db.create_document(
            {'_id': 'julia006', 'name': 'julia', 'age': 6}
        )
        try:
            filename = 'attachment-{0}{1}'.format(unicode_(uuid.uuid4()), '.jpg')
            data = None
            with open(find_fixture('smile.jpg'), 'rb') as f:
                data = f.read()
                resp = doc.put_attachment(filename,'image/jpeg', data)
            with open(find_fixture(filename), 'wb') as f:
                binary_attachment = doc.get_attachment(filename, write_to=f)
                self.assertEqual(binary_attachment, data)
            with open(find_fixture(filename), 'rb') as f:
                self.assertEqual(f.read(), data)
        finally:
            os.remove(find_fixture(filename))

    def test_attachment_management(self):
        """
        Test the adding, retrieving, updating, and deleting of attachments
        """
        doc = self.db.create_document(
            {'_id': 'julia006', 'name': 'julia', 'age': 6}
        )
        attachment = StringIO()
        try:
            attachment.write('This is line one of the attachment.\n')
            attachment.write('This is line two of the attachment.\n')
            self.assertTrue(doc['_rev'].startswith('1-'))
            # Test adding an attachment
            resp = doc.put_attachment(
                'attachment.txt',
                'text/plain',
                attachment.getvalue()
            )
            self.assertTrue(resp['ok'])
            self.assertTrue(resp['rev'].startswith('2-'))
            self.assertEqual(doc['_rev'], resp['rev'])
            self.assertTrue(
                all(x in list(doc.keys()) for x in [
                    '_id',
                    '_rev',
                    'name',
                    'age',
                    '_attachments'
                ])
            )
            self.assertTrue(
                all(x in list(doc['_attachments'].keys()) for x in [
                    'attachment.txt'
                ])
            )
            orig_size = doc['_attachments']['attachment.txt']['length']
            self.assertEqual(orig_size, len(attachment.getvalue()))
            # Confirm that the local document dictionary matches 
            # the document on the database.
            expected = Document(self.db, 'julia006')
            expected.fetch()
            # Test retrieving an attachment
            self.assertEqual(
                doc.get_attachment('attachment.txt', attachment_type='text'),
                attachment.getvalue()
            )
            # Test update an attachment
            attachment.write('This is line three of the attachment.\n')
            resp = doc.put_attachment(
                'attachment.txt',
                'text/plain',
                attachment.getvalue()
            )
            self.assertTrue(resp['ok'])
            self.assertTrue(resp['rev'].startswith('3-'))
            self.assertEqual(doc['_rev'], resp['rev'])
            self.assertTrue(
                all(x in list(doc.keys()) for x in [
                    '_id',
                    '_rev',
                    'name',
                    'age',
                    '_attachments'
                ])
            )
            self.assertTrue(
                all(x in list(doc['_attachments'].keys()) for x in [
                    'attachment.txt'
                ])
            )
            updated_size = doc['_attachments']['attachment.txt']['length']
            self.assertTrue(updated_size > orig_size)
            self.assertEqual(updated_size, len(attachment.getvalue()))
            self.assertEqual(
                doc.get_attachment('attachment.txt', attachment_type='text'),
                attachment.getvalue()
            )
            # Confirm that the local document dictionary matches 
            # the document on the database.
            expected = Document(self.db, 'julia006')
            expected.fetch()
            # Test delete attachments
            # Add a second attachment so we can fully test
            # delete functionality.
            resp = doc.put_attachment(
                'attachment2.txt',
                'text/plain',
                attachment.getvalue()
            )
            # Test deleting an attachment from a document
            # with multiple atatchments.
            resp = doc.delete_attachment('attachment.txt')
            self.assertTrue(resp['ok'])
            self.assertTrue(resp['rev'].startswith('5-'))
            self.assertEqual(doc['_rev'], resp['rev'])
            self.assertTrue(
                all(x in list(doc.keys()) for x in [
                    '_id',
                    '_rev',
                    'name',
                    'age',
                    '_attachments'
                ])
            )
            # Confirm that the local document dictionary matches 
            # the document on the database.
            expected = Document(self.db, 'julia006')
            expected.fetch()
            self.assertEqual(doc, expected)
            # Test deleting an attachment from a document
            # with a single attachment.
            resp = doc.delete_attachment('attachment2.txt')
            self.assertTrue(resp['ok'])
            self.assertTrue(resp['rev'].startswith('6-'))
            self.assertEqual(doc['_rev'], resp['rev'])
            self.assertTrue(
                all(x in list(doc.keys()) for x in [
                    '_id',
                    '_rev',
                    'name',
                    'age'
                ])
            )
            # Confirm that the local document dictionary matches 
            # the document on the database.
            expected = Document(self.db, 'julia006')
            expected.fetch()
            self.assertEqual(doc, expected)
        finally:
            attachment.close()

    def test_document_request_fails_after_client_disconnects(self):
        """
        Test that after disconnecting from a client any objects created based
        on that client are not able to make requests.
        """
        self.client.connect()
        doc = Document(self.db, 'julia001')
        doc.save()
        self.client.disconnect()

        try:
            with self.assertRaises(AttributeError):
                doc.fetch()
            self.assertIsNone(doc.r_session)
        finally:
            self.client.connect()

if __name__ == '__main__':
    unittest.main()
