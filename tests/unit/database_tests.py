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
_database_tests_

database module - Unit tests for CouchDatabase and CloudantDatabase classes

See configuration options for environment variables in unit_t_db_base
module docstring.

"""

import unittest
import mock
import requests
import posixpath
import os
import uuid

from cloudant.result import Result, QueryResult
from cloudant.error import CloudantArgumentError, CloudantDatabaseException
from cloudant.document import Document
from cloudant.design_document import DesignDocument
from cloudant.security_document import SecurityDocument
from cloudant.index import Index, TextIndex, SpecialIndex
from cloudant.feed import Feed, InfiniteFeed
from tests.unit._test_util import LONG_NUMBER

from .unit_t_db_base import UnitTestDbBase
from .. import unicode_

class CloudantDatabaseExceptionTests(unittest.TestCase):
    """
    Ensure CloudantDatabaseException functions as expected.
    """

    def test_raise_without_code(self):
        """
        Ensure that a default exception/code is used if none is provided.
        """
        with self.assertRaises(CloudantDatabaseException) as cm:
            raise CloudantDatabaseException()
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_using_invalid_code(self):
        """
        Ensure that a default exception/code is used if invalid code is provided.
        """
        with self.assertRaises(CloudantDatabaseException) as cm:
            raise CloudantDatabaseException('foo')
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_without_args(self):
        """
        Ensure that a default exception/code is used if the message requested
        by the code provided requires an argument list and none is provided.
        """
        with self.assertRaises(CloudantDatabaseException) as cm:
            raise CloudantDatabaseException(400)
        self.assertEqual(cm.exception.status_code, 100)

    def test_raise_with_proper_code_and_args(self):
        """
        Ensure that the requested exception is raised.
        """
        with self.assertRaises(CloudantDatabaseException) as cm:
            raise CloudantDatabaseException(400, 'foo')
        self.assertEqual(cm.exception.status_code, 400)

class DatabaseTests(UnitTestDbBase):
    """
    CouchDatabase/CloudantDatabase unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(DatabaseTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(DatabaseTests, self).tearDown()

    def test_constructor(self):
        """
        Test instantiating a database
        """
        self.assertEqual(self.db.client, self.client)
        self.assertEqual(self.db.database_name, self.test_dbname)
        self.assertEqual(self.db.r_session, self.client.r_session)
        self.assertIsInstance(self.db.result, Result)

    def test_bulk_docs_uses_custom_encoder(self):
        """
        Test that the bulk_docs method uses the custom encoder
        """
        self.set_up_client(auto_connect=True, encoder="AEncoder")
        docs = [
            {'_id': 'julia{0:03d}'.format(i), 'name': 'julia', 'age': i}
            for i in range(3)
        ]
        database = self.client[self.test_dbname]
        with self.assertRaises(TypeError):
            # since the encoder is a str a type error should be thrown.
            database.bulk_docs(docs)

    def test_missing_revisions_uses_custom_encoder(self):
        """
        Test that missing_revisions uses the custom encoder.
        """
        revs = ['1-1', '2-1', '3-1']
        self.set_up_client(auto_connect=True, encoder="AEncoder")
        database = self.client[self.test_dbname]
        with self.assertRaises(TypeError):
            # since the encoder is a str a type error should be thrown.
            database.missing_revisions('no-such-doc', *revs)

    def test_revs_diff_uses_custom_encoder(self):
        """
        Test that revisions_diff uses the custom encoder.
        """
        revs = ['1-1', '2-1', '3-1']
        self.set_up_client(auto_connect=True, encoder="AEncoder")
        database = self.client[self.test_dbname]
        with self.assertRaises(TypeError):
            database.revisions_diff('no-such-doc', *revs)

    def test_retrieve_db_url(self):
        """
        Test retrieving the database URL
        """
        self.assertEqual(
            self.db.database_url,
            posixpath.join(self.client.server_url, self.test_dbname)
            )

    def test_retrieve_creds(self):
        """
        Test retrieving client credentials. The client credentials are None if
        CouchDB Admin Party mode was selected.
        """
        if self.client.admin_party:
            self.assertIsNone(self.db.creds)
        else:
            expected_keys = ['basic_auth', 'user_ctx']
            self.assertTrue(
                all(x in expected_keys for x in self.db.creds.keys())
            )
            self.assertTrue(self.db.creds['basic_auth'].startswith('Basic'))
            self.assertEqual(self.db.creds['user_ctx']['name'], self.user)

    def test_exists(self):
        """
        Tests that the result of True is expected when the database exists,
        and False is expected when the database is nonexistent remotely.
        """
        self.assertTrue(self.db.exists())
        # Construct a database object that does not exist remotely
        fake_db = self.client._DATABASE_CLASS(self.client, 'no-such-db')
        self.assertFalse(fake_db.exists())

    def test_exists_raises_httperror(self):
        """
        Test database exists raises an HTTPError.
        """
        # Mock HTTPError when running against CouchDB and Cloudant
        resp = requests.Response()
        resp.status_code = 400
        self.client.r_session.head = mock.Mock(return_value=resp)
        with self.assertRaises(requests.HTTPError) as cm:
            self.db.exists()
        err = cm.exception
        self.assertEqual(err.response.status_code, 400)
        self.client.r_session.head.assert_called_with(self.db.database_url)

    def test_create_db_delete_db(self):
        """
        Test creating and deleting a database
        """
        dbname = self.dbname()
        db = self.client._DATABASE_CLASS(self.client, dbname)
        try:
            db.create()
            self.assertTrue(db.exists())
            # No issue should arise if attempting to create existing database
            db_2 = db.create()
            self.assertEqual(db, db_2)
            # If we use throw_on_exists=True, it will raise a
            # CloudantDatabaseException if the database already exists.
            with self.assertRaises(CloudantDatabaseException) as cm:
                db.create(throw_on_exists=True)
            self.assertEqual(cm.exception.status_code, 412)
        except Exception as err:
            self.fail('Exception {0} was raised.'.format(str(err)))
        finally:
            db.delete()
            self.assertFalse(db.exists())

    def test_delete_exception(self):
        """
        Test deleting a database that does not exist
        """
        try:
            fake_db = self.client._DATABASE_CLASS(self.client, 'no-such-db')
            fake_db.delete()
            self.fail('Above statement should raise an Exception')
        except requests.HTTPError as err:
            self.assertEqual(err.response.status_code, 404)

    def test_retrieve_db_metadata(self):
        """
        Test retrieving the database metadata information.  The metadata values
        may differ slightly each time it is retrieved such as is the case with
        the update sequence, however, the metadata keys should always remain the
        same.  Therefore comparing keys is a valid test of this functionality.
        """
        resp = self.db.r_session.get(
            posixpath.join(self.client.server_url, self.test_dbname)
            )
        expected = resp.json()
        actual = self.db.metadata()
        self.assertListEqual(list(actual.keys()), list(expected.keys()))

    def test_retrieve_document_count(self):
        """
        Test retrieving the number of documents currently in the database
        """
        self.populate_db_with_documents(6)
        self.assertEqual(self.db.doc_count(), 6)

    def test_create_document_with_id(self):
        """
        Test creating a document using a supplied document id
        """
        data = {'_id': 'julia06', 'name': 'julia', 'age': 6}
        doc = self.db.create_document(data)
        self.assertEqual(self.db['julia06'], doc)
        self.assertEqual(doc['_id'], data['_id'])
        self.assertTrue(doc['_rev'].startswith('1-'))
        self.assertEqual(doc['name'], data['name'])
        self.assertEqual(doc['age'], data['age'])
        self.assertIsInstance(doc, Document)
        self.assertIsInstance(self.db['julia06'], Document)
        try:
            self.db.create_document(data, throw_on_exists=True)
            self.fail('Above statement should raise a CloudantException')
        except CloudantDatabaseException as err:
            self.assertEqual(
                str(err),
                'Document with id julia06 already exists.'
                )

    def test_create_document_without_id(self):
        """
        Test creating a document without supplying a document id
        """
        data = {'name': 'julia', 'age': 6}
        doc = self.db.create_document(data)
        self.assertEqual(self.db[doc['_id']], doc)
        self.assertTrue(doc['_rev'].startswith('1-'))
        self.assertEqual(doc['name'], data['name'])
        self.assertEqual(doc['age'], data['age'])
        self.assertIsInstance(doc, Document)
        self.assertIsInstance(self.db[doc['_id']], Document)

    def test_create_design_document(self):
        """
        Test creating a document using a supplied document id
        """
        data = {'_id': '_design/julia06', 'name': 'julia', 'age': 6}
        doc = self.db.create_document(data)
        self.assertEqual(self.db['_design/julia06'], doc)
        self.assertEqual(doc['_id'], data['_id'])
        self.assertTrue(doc['_rev'].startswith('1-'))
        self.assertEqual(doc['name'], data['name'])
        self.assertEqual(doc['age'], data['age'])
        self.assertEqual(doc.views, dict())
        self.assertIsInstance(doc, DesignDocument)
        self.assertIsInstance(self.db['_design/julia06'], DesignDocument)

    def test_create_empty_document(self):
        """
        Test creating an empty document
        """
        empty_doc = self.db.new_document()
        self.assertEqual(self.db[empty_doc['_id']], empty_doc)
        self.assertTrue(all(x in ['_id', '_rev'] for x in empty_doc.keys()))
        self.assertTrue(empty_doc['_rev'].startswith('1-'))

    def test_retrieve_design_documents(self):
        """
        Test retrieving all design documents
        """
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        data = {'_id': '_design/ddoc01','views': {'view01': {"map": map_func}}}
        ddoc1 = self.db.create_document(data)
        data = {'_id': '_design/ddoc02','views': {'view02': {"map": map_func}}}
        ddoc2 = self.db.create_document(data)
        raw_ddocs = self.db.design_documents()
        self.assertEqual(len(raw_ddocs), 2)
        self.assertTrue(
            all(x in [raw_ddocs[0]['key'], raw_ddocs[1]['key']]
                for x in self.db.keys()
                )
            )
        self.assertTrue(
            all(x in [raw_ddocs[0]['id'], raw_ddocs[1]['id']]
                for x in self.db.keys()
                )
            )
        self.assertTrue(
            all(x in [raw_ddocs[0]['doc'], raw_ddocs[1]['doc']]
                for x in [ddoc1, ddoc2]
                )
            )

    def test_retrieve_design_document_list(self):
        """
        Test retrieving a list of design document names
        """
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        data = {'_id': '_design/ddoc01','views': {'view01': {"map": map_func}}}
        self.db.create_document(data)
        data = {'_id': '_design/ddoc02','views': {'view02': {"map": map_func}}}
        self.db.create_document(data)
        ddoc_list = self.db.list_design_documents()
        self.assertTrue(all(x in ddoc_list for x in self.db.keys()))

    def test_retrieve_design_document(self):
        """
        Test retrieve a specific design document
        """
        # Get an empty design document object that does not exist remotely
        local_ddoc = self.db.get_design_document('_design/ddoc01')
        self.assertEqual(local_ddoc, {'_id': '_design/ddoc01', 'indexes': {},
                                      'views': {}, 'lists': {}, 'shows': {}})
        # Add the design document to the database
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        local_ddoc.add_view('view01', map_func)
        local_ddoc.save()

        # Get the recently created design document that now exists remotely
        ddoc = self.db.get_design_document('_design/ddoc01')
        self.assertEqual(ddoc, local_ddoc)

    def test_get_security_document(self):
        """
        Test retrieving the database security document
        """
        self.load_security_document_data()
        sdoc = self.db.get_security_document()
        self.assertIsInstance(sdoc, SecurityDocument)
        self.assertDictEqual(sdoc, self.sdoc)

    def test_retrieve_view_results(self):
        """
        Test retrieving Result wrapped output from a design document view
        """
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        data = {'_id': '_design/ddoc01','views': {'view01': {"map": map_func}}}
        self.db.create_document(data)
        self.populate_db_with_documents()

        # Test with default Result
        rslt = self.db.get_view_result('_design/ddoc01', 'view01')
        self.assertIsInstance(rslt, Result)
        self.assertEqual(rslt[:1], rslt['julia000'])

        # Test with custom Result
        rslt = self.db.get_view_result(
            '_design/ddoc01',
            'view01',
            descending=True,
            reduce=False)
        self.assertIsInstance(rslt, Result)
        self.assertEqual(rslt[:1], rslt['julia099'])

    def test_retrieve_raw_view_results(self):
        """
        Test retrieving raw output from a design document view
        """
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        data = {'_id': '_design/ddoc01','views': {'view01': {"map": map_func}}}
        self.db.create_document(data)
        self.populate_db_with_documents()

        raw_rslt = self.db.get_view_result(
            '_design/ddoc01', 'view01', raw_result=True)
        self.assertIsInstance(raw_rslt, dict)
        self.assertEqual(len(raw_rslt.get('rows')), 100)

    def test_all_docs_post(self):
        """
        Test the all_docs POST request functionality using keys param
        """
        # Create 200 documents with ids julia000, julia001, julia002, ..., julia199
        self.populate_db_with_documents(200)
        # Generate keys list for every other document created
        # with ids julia000, julia002, julia004, ..., julia198
        keys_list = ['julia{0:03d}'.format(i) for i in range(0, 200, 2)]
        self.assertEqual(len(keys_list), 100)
        rows = self.db.all_docs(keys=keys_list).get('rows')
        self.assertEqual(len(rows), 100)
        keys_returned = [row['key'] for row in rows]
        self.assertTrue(all(x in keys_returned for x in keys_list))

    def test_all_docs_post_multiple_params(self):
        """
        Test the all_docs POST request functionality using keys and other params
        """
        # Create 200 documents with ids julia000, julia001, julia002, ..., julia199
        self.populate_db_with_documents(200)
        # Generate keys list for every other document created
        # with ids julia000, julia002, julia004, ..., julia198
        keys_list = ['julia{0:03d}'.format(i) for i in range(0, 200, 2)]
        self.assertEqual(len(keys_list), 100)
        data = self.db.all_docs(limit=3, skip=10, keys=keys_list)
        self.assertEqual(len(data.get('rows')), 3)
        self.assertEqual(data['rows'][0]['key'], 'julia020')
        self.assertEqual(data['rows'][1]['key'], 'julia022')
        self.assertEqual(data['rows'][2]['key'], 'julia024')

    def test_all_docs_get(self):
        """
        Test the all_docs GET request functionality
        """
        self.populate_db_with_documents()
        data = self.db.all_docs(limit=3, skip=10)
        self.assertEqual(len(data.get('rows')), 3)
        self.assertEqual(data['rows'][0]['key'], 'julia010')
        self.assertEqual(data['rows'][1]['key'], 'julia011')
        self.assertEqual(data['rows'][2]['key'], 'julia012')

    def test_all_docs_get_with_long_type(self):
        """
        Test the all_docs GET request functionality
        """
        self.populate_db_with_documents()
        data = self.db.all_docs(limit=LONG_NUMBER, skip=10)
        self.assertEqual(len(data.get('rows')), 1)
        self.assertEqual(data['rows'][0]['key'], 'julia010')
        data = self.db.all_docs(limit=1, skip=LONG_NUMBER)
        self.assertEqual(len(data.get('rows')), 1)

    def test_custom_result_context_manager(self):
        """
        Test using the database custom result context manager
        """
        self.populate_db_with_documents()
        with self.db.custom_result(startkey='julia010', endkey='julia012') as rslt:
            self.assertIsInstance(rslt, Result)
            keys_returned = [i['key'] for i in rslt]
            expected_keys = ['julia010', 'julia011', 'julia012']
            self.assertTrue(all(x in keys_returned for x in expected_keys))

    def test_keys(self):
        """
        Test retrieving the document keys from the database
        """
        self.assertEqual(list(self.db.keys()), [])
        self.populate_db_with_documents(3)
        self.assertEqual(
            self.db.keys(remote=True),
            ['julia000', 'julia001', 'julia002']
            )

    def test_get_non_existing_doc_via_getitem(self):
        """
        Test __getitem__ when retrieving a non-existing document
        """
        try:
            doc = self.db['no_such_doc']
            self.fail('Above statement should raise a KeyError')
        except KeyError:
            pass

    def test_get_db_via_getitem(self):
        """
        Test __getitem__ when retrieving a document
        """

        # Add a design document
        map_func = 'function(doc) {\n emit(doc._id, 1); \n}'
        expected_ddoc = self.db.get_design_document('_design/ddoc01')
        expected_ddoc.add_view('view01', map_func)
        expected_ddoc.save()

        # Add three standard documents
        self.populate_db_with_documents(3)

        # Test __get_item__ for standard document
        doc = self.db['julia001']
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.get('_id'), 'julia001')
        self.assertTrue(doc.get('_rev').startswith('1-'))
        self.assertEqual(doc.get('name'), 'julia')
        self.assertEqual(doc.get('age'), 1)

        # Test __get_item__ for design document
        ddoc = self.db['_design/ddoc01']
        self.assertIsInstance(ddoc, DesignDocument)
        self.assertTrue(ddoc, expected_ddoc)

    def test_document_iteration_under_fetch_limit(self):
        """
        Test __iter__ works as expected when the number of documents in
        the database is less than the database fetch limit
        """
        docs = []

        # Check iterating when no documents exist
        for doc in self.db:
            self.fail('There should be no documents in the database yet!!')
        # Check that iteration yields appropriate contents
        self.populate_db_with_documents(3)
        age = 0
        for doc in self.db:
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc['_id'], 'julia{0:03d}'.format(age))
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(doc['name'], 'julia')
            self.assertEqual(doc['age'], age)
            docs.append(doc)
            age += 1
        self.assertEqual(len(docs), 3)
        # Check that the local database object has been populated
        # with the appropriate documents
        expected_keys = ['julia{0:03d}'.format(i) for i in range(3)]
        self.assertTrue(all(x in self.db.keys()for x in expected_keys))
        for id in self.db.keys():
            doc = self.db.get(id)
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc['_id'], id)
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(doc['name'], 'julia')
            self.assertEqual(doc['age'], int(id[len(id) - 3 : len(id)]))

    def test_document_iteration_over_fetch_limit(self):
        """
        Test __iter__ works as expected when the number of documents in
        the database is more than the database fetch limit
        """
        docs = []
        # Check iterating when no documents exist
        for doc in self.db:
            self.fail('There should be no documents in the database yet!!')
        # Check that iteration yields appropriate contents
        self.populate_db_with_documents(103)
        age = 0
        for doc in self.db:
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc['_id'], 'julia{0:03d}'.format(age))
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(doc['name'], 'julia')
            self.assertEqual(doc['age'], age)
            docs.append(doc)
            age += 1
        self.assertEqual(len(docs), 103)
        # Check that the local database object has been populated
        # with the appropriate documents
        expected_keys = ['julia{0:03d}'.format(i) for i in range(103)]
        self.assertTrue(all(x in self.db.keys()for x in expected_keys))
        for id in self.db.keys():
            doc = self.db.get(id)
            self.assertIsInstance(doc, Document)
            self.assertEqual(doc['_id'], id)
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(doc['name'], 'julia')
            self.assertEqual(doc['age'], int(id[len(id) - 3: len(id)]))

    def test_document_iteration_returns_valid_documents(self):
        """
        This test will check that the __iter__ method returns documents that are
        valid Document or DesignDocument objects and that they can be managed
        remotely.  In this test we will delete the documents as part of the test
        to ensure that remote management is working as expected and confirming
        that the documents are valid.
        """
        self.populate_db_with_documents(3)
        with DesignDocument(self.db, '_design/ddoc001') as ddoc:
            ddoc.add_view('view001', 'function (doc) {\n  emit(doc._id, 1);\n}')
        docs = []
        ddocs = []
        for doc in self.db:
            # A valid document must have a document_url
            self.assertEqual(
                doc.document_url,
                posixpath.join(self.db.database_url, doc['_id'])
            )
            if isinstance(doc, DesignDocument):
                self.assertEqual(doc['_id'], '_design/ddoc001')
                ddocs.append(doc)
            elif isinstance(doc, Document):
                self.assertTrue(
                    doc['_id'] in ['julia000', 'julia001', 'julia002']
                )
                docs.append(doc)
            doc.delete()

        # Confirm successful deletions
        for doc in self.db:
            self.fail('All documents should have been deleted!!!')

        # Confirm that the correct number of Document (3) and DesignDocument (1)
        # objects were returned
        self.assertEqual(len(docs), 3)
        self.assertEqual(len(ddocs), 1)

    def test_bulk_docs_creation(self):
        docs = [
            {'_id': 'julia{0:03d}'.format(i), 'name': 'julia', 'age': i}
            for i in range(3)
        ]
        results = self.db.bulk_docs(docs)
        self.assertEqual(len(results), 3)
        i = 0
        for result in results:
            self.assertEqual(result['id'], 'julia{0:03d}'.format(i))
            self.assertTrue(result['rev'].startswith('1-'))
            i += 1

    def test_bulk_docs_update(self):
        """
        Test update of documents in bulk
        """
        self.populate_db_with_documents(3)
        docs = []
        for doc in self.db:
            doc['name'] = 'jules'
            docs.append(doc)
        results = self.db.bulk_docs(docs)
        self.assertEqual(len(results), 3)
        i = 0
        for result in results:
            self.assertEqual(result['id'], 'julia{0:03d}'.format(i))
            self.assertTrue(result['rev'].startswith('2-'))
            i += 1
        age = 0
        for doc in self.db:
            self.assertEqual(doc['_id'], 'julia{0:03d}'.format(age))
            self.assertTrue(doc['_rev'].startswith('2-'))
            self.assertEqual(doc['name'], 'jules')
            self.assertEqual(doc['age'], age)
            age += 1
        self.assertEqual(age, 3)

    def test_missing_revisions(self):
        """
        Test retrieving missing revisions
        """
        doc = self.db.create_document(
            {'_id': 'julia006', 'name': 'julia', 'age': 6}
        )
        # Test when the doc is not found
        revs = ['1-1', '2-1', '3-1']
        self.assertEqual(self.db.missing_revisions('no-such-doc', *revs), revs)
        # Test all revs not found
        self.assertEqual(self.db.missing_revisions('julia006', *revs), revs)
        # Test when some revs not found
        self.assertEqual(
            self.db.missing_revisions('julia006', doc['_rev'], *revs), revs
        )
        # Test no missing revs
        self.assertEqual(self.db.missing_revisions('julia006', doc['_rev']), [])

    def test_revisions_diff(self):
        """
        Test retrieving differences in revisions
        """
        doc = self.db.create_document(
            {'_id': 'julia006', 'name': 'julia', 'age': 6}
        )
        # Test when the doc is not found
        revs = ['1-1', '2-1', '3-1']
        self.assertEqual(
            self.db.revisions_diff('no-such-doc', *revs),
            {'no-such-doc': {'missing': revs}}
        )
        # Test differences
        self.assertEqual(
            self.db.revisions_diff('julia006', *revs),
            {'julia006': {'missing': revs, 'possible_ancestors': [doc['_rev']]}}
        )
        # Test no differences
        self.assertEqual(self.db.revisions_diff('julia006', doc['_rev']), {})

    def test_get_set_revision_limit(self):
        """
        Test setting and getting revision limits
        """
        limit = self.db.get_revision_limit()
        self.assertIsInstance(limit, int)
        self.assertEqual(self.db.set_revision_limit(1234), {'ok': True})
        new_limit = self.db.get_revision_limit()
        self.assertNotEqual(new_limit, limit)
        self.assertEqual(new_limit, 1234)

    @unittest.skipIf(os.environ.get('RUN_CLOUDANT_TESTS'),
        'Skipping since view cleanup is automatic in Cloudant.')
    def test_view_clean_up(self):
        """
        Test cleaning up old view files
        """
        self.assertEqual(self.db.view_cleanup(), {'ok': True})

    def test_changes_feed_call(self):
        """
        Test that changes() method call constructs and returns a Feed object
        """
        changes = self.db.changes(limit=100)
        self.assertIs(type(changes), Feed)
        self.assertEqual(changes._url, '/'.join([self.db.database_url, '_changes']))
        self.assertIsInstance(changes._r_session, requests.Session)
        self.assertFalse(changes._raw_data)
        self.assertDictEqual(changes._options, {'limit': 100})

    def test_changes_inifinite_feed_call(self):
        """
        Test that infinite_changes() method call constructs and returns an
        InfiniteFeed object
        """
        changes = self.db.infinite_changes()
        self.assertIsInstance(changes, InfiniteFeed)
        self.assertEqual(changes._url, '/'.join([self.db.database_url, '_changes']))
        self.assertIsInstance(changes._r_session, requests.Session)
        self.assertFalse(changes._raw_data)
        self.assertDictEqual(changes._options, {'feed': 'continuous'})

    def test_get_list_function_result_with_invalid_argument(self):
        """
        Test get_list_result by passing in invalid arguments
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.get_list_function_result('ddoc001', 'list001', 'view001', foo={'bar': 'baz'})
        err = cm.exception
        self.assertEqual(str(err), 'Invalid argument foo')

    def test_get_list_function_result(self):
        """
        Test get_list_result executes a list function against a view's MapReduce
        function.
        """
        self.populate_db_with_documents()
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.add_view('view001', 'function (doc) {\n  emit(doc._id, 1);\n}')
        ddoc.add_list_function(
            'list001',
            'function(head, req) { provides(\'html\', function() '
            '{var html = \'<html><body><ol>\\n\'; while (row = getRow()) '
            '{ html += \'<li>\' + row.key + \':\' + row.value + \'</li>\\n\';} '
            'html += \'</ol></body></html>\'; return html; }); }')
        ddoc.save()
        # Execute list function
        resp = self.db.get_list_function_result(
            '_design/ddoc001',
            'list001',
            'view001',
            limit=5
        )
        self.assertEqual(
            resp,
            '<html><body><ol>\n'
            '<li>julia000:1</li>\n'
            '<li>julia001:1</li>\n'
            '<li>julia002:1</li>\n'
            '<li>julia003:1</li>\n'
            '<li>julia004:1</li>\n'
            '</ol></body></html>'
        )

    def test_get_show_result(self):
        """
        Test get_show_result executes a show function against a document.
        """
        self.populate_db_with_documents()
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc.add_show_function(
            'show001',
            'function(doc, req) { '
            'if (doc) { return \'Hello from \' + doc._id + \'!\'; } '
            'else { return \'Hello, world!\'; } }')
        ddoc.save()
        doc = Document(self.db, 'doc001')
        doc.save()
        # Execute show function
        resp = self.db.get_show_function_result(
            '_design/ddoc001',
            'show001',
            'doc001'
        )
        self.assertEqual(
            resp,
            'Hello from doc001!'
        )

    def test_create_doc_with_update_handler(self):
        """
        Test update_handler_result executes an update handler function
        that creates a new document
        """
        self.populate_db_with_documents()
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc['updates'] = {
            'update001': 'function(doc, req) { if (!doc) { var new_doc = req.form; '
                         'new_doc._id = \'testDoc\'; return [new_doc, '
                         '\'Created new doc: \' + JSON.stringify(new_doc)]; }} '
        }

        ddoc.save()
        resp = self.db.update_handler_result('ddoc001', 'update001', data={'message': 'hello'})
        self.assertEqual(
            resp,
            'Created new doc: {"message":"hello","_id":"testDoc"}'
        )

    def test_update_doc_with_update_handler(self):
        """
        Test update_handler_result executes an update handler function
        that updates a document with query parameters
        """
        self.populate_db_with_documents()
        ddoc = DesignDocument(self.db, '_design/ddoc001')
        ddoc['updates'] = {
            'update001': 'function(doc, req) { '
                         'var field = req.query.field; '
                         'var value = req.query.value; '
                         'var new_doc = doc; '
                         'doc[field] = value; '
                         'for(var key in req.form) doc[key]=req.form[key]; '
                         'var message = \'set \'+field+\' to \'+value'
                         '+\' and add data \'+ JSON.stringify(req.form); '
                         'return [doc, message]; } '
        }
        ddoc.save()
        resp = self.db.update_handler_result('ddoc001', 'update001', 'julia001',
                                             field='new_field', value='new_value',
                                             data={'message': 'hello'})
        self.assertEqual(
            resp,
            'set new_field to new_value and add data {"message":"hello"}'
        )
        ddoc_remote = Document(self.db, 'julia001')
        ddoc_remote.fetch()
        self.assertEqual(
            ddoc_remote,
            {'age': 1, 'name': 'julia', 'new_field': 'new_value',
             '_rev': ddoc_remote['_rev'], '_id': 'julia001',
             'message': 'hello'}
        )

    def test_update_handler_raises_httperror(self):
        """
        Test update_handler_result raises an HTTPError.
        """
        # Mock HTTPError when running against CouchDB or Cloudant
        resp = requests.Response()
        resp.status_code = 400
        self.client.r_session.put = mock.Mock(return_value=resp)
        with self.assertRaises(requests.HTTPError) as cm:
            self.db.update_handler_result('ddoc001', 'update001', 'julia001',
                                          field='new_field', value='new_value',
                                          data={'message': 'hello'})
        err = cm.exception
        self.assertEqual(err.response.status_code, 400)
        ddoc = DesignDocument(self.db, 'ddoc001')
        self.client.r_session.put.assert_called_with(
            '/'.join([ddoc.document_url, '_update', 'update001', 'julia001']),
            data={'message': 'hello'},
            params={'field': 'new_field', 'value': 'new_value'})

    def test_database_request_fails_after_client_disconnects(self):
        """
        Test that after disconnecting from a client any objects created based
        on that client are not able to make requests.
        """
        self.client.disconnect()

        try:
            with self.assertRaises(AttributeError):
                self.db.metadata()
            self.assertIsNone(self.db.r_session)
        finally:
            self.client.connect()

@unittest.skipUnless(
    os.environ.get('RUN_CLOUDANT_TESTS') is not None,
    'Skipping Cloudant specific Database tests'
)
class CloudantDatabaseTests(UnitTestDbBase):
    """
    Cloudant specific Database unit tests
    """

    def setUp(self):
        """
        Set up test attributes
        """
        super(CloudantDatabaseTests, self).setUp()
        self.db_set_up()

    def tearDown(self):
        """
        Reset test attributes
        """
        self.db_tear_down()
        super(CloudantDatabaseTests, self).tearDown()

    def test_share_database_uses_custom_encoder(self):
        """
        Test that share_database uses custom encoder
        """
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        self.set_up_client(auto_connect=True, encoder="AEncoder")
        database = self.client[self.test_dbname]
        with self.assertRaises(TypeError):
            database.share_database(share)


    def test_unshare_database_uses_custom_encoder(self):
        """
        Test that unshare_database uses custom encoder
        """
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        self.set_up_client(auto_connect=True, encoder="AEncoder")
        database = self.client[self.test_dbname]
        with self.assertRaises(TypeError):
            database.unshare_database(share)

    def test_security_document(self):
        """
        Test the retrieval of the security document.
        """
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        self.db.share_database(share)
        expected = {'cloudant': {share: ['_reader']}}
        self.assertDictEqual(self.db.security_document(), expected)

    def test_share_database_default_permissions(self):
        """
        Test the sharing of a database applying default permissions.
        """
        self.assertDictEqual(self.db.security_document(), dict())
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        self.db.share_database(share)
        expected = {'cloudant': {share: ['_reader']}}
        self.assertDictEqual(self.db.security_document(), expected)

    def test_share_database(self):
        """
        Test the sharing of a database.
        """
        self.assertDictEqual(self.db.security_document(), dict())
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        self.db.share_database(share, ['_writer'])
        expected = {'cloudant': {share: ['_writer']}}
        self.assertDictEqual(self.db.security_document(), expected)

    def test_share_database_with_redundant_role_entries(self):
        """
        Test the sharing of a database works when the list of roles contains
        valid entries but some entries are duplicates.
        """
        self.assertDictEqual(self.db.security_document(), dict())
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        self.db.share_database(share, ['_writer', '_writer'])
        expected = {'cloudant': {share: ['_writer']}}
        self.assertDictEqual(self.db.security_document(), expected)

    def test_share_database_invalid_role(self):
        """
        Test the sharing of a database fails when provided an invalid role.
        """
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.share_database(share, ['_writer', '_invalid_role'])
        err = cm.exception
        self.assertEqual(
            str(err),
            'Invalid role(s) provided: '
            '[\'_writer\', \'_invalid_role\'].  Valid roles are: '
            '[\'_reader\', \'_writer\', \'_admin\', \'_replicator\', '
            '\'_db_updates\', \'_design\', \'_shards\', \'_security\']'
        )

    def test_share_database_empty_role_list(self):
        """
        Test the sharing of a database fails when provided an empty role list.
        """
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.share_database(share, [])
        err = cm.exception
        self.assertEqual(
            str(err),
            'Invalid role(s) provided: [].  Valid roles are: '
            '[\'_reader\', \'_writer\', \'_admin\', \'_replicator\', '
            '\'_db_updates\', \'_design\', \'_shards\', \'_security\']'
        )

    def test_unshare_database(self):
        """
        Test the un-sharing of a database from a specified user.
        """
        share = 'user-{0}'.format(unicode_(uuid.uuid4()))
        self.db.share_database(share)
        expected = {'cloudant': {share: ['_reader']}}
        self.assertDictEqual(self.db.security_document(), expected)
        self.assertDictEqual(self.db.unshare_database(share), {'ok': True})
        self.assertDictEqual(self.db.security_document(), {'cloudant': dict()})

    def test_retrieve_shards(self):
        shards = self.db.shards()
        self.assertTrue(all(x in shards.keys() for x in ['shards']))
        self.assertIsInstance(shards['shards'], dict)

    def test_get_raw_query_result(self):
        """
        Test that retrieving the raw JSON response for a query works as expected
        """
        self.populate_db_with_documents(100)
        result = self.db.get_query_result(
            {'$and': [
                {'_id': {'$gte': 'julia001'}},
                {'_id': {'$lt': 'julia005'}}
            ]},
            ['_id', '_rev'],
            True
        )
        self.assertNotIsInstance(result, QueryResult)
        self.assertIsInstance(result, dict)
        self.assertEqual(
            [doc['_id'] for doc in result['docs']],
            ['julia001', 'julia002', 'julia003', 'julia004']
        )

    def test_get_query_result_with_kwargs(self):
        """
        Test that retrieving the QueryResult for a query works as expected when
        additional options are added via kwargs
        """
        self.populate_db_with_documents(100)
        result = self.db.get_query_result(
            {'$and': [
                {'_id': {'$gte': 'julia001'}},
                {'_id': {'$lt': 'julia005'}}
            ]},
            ['_id', '_rev'],
            sort=[{'_id': 'desc'}]
        )
        self.assertIsInstance(result, QueryResult)
        self.assertEqual(
            [doc['_id'] for doc in result],
            ['julia004', 'julia003', 'julia002', 'julia001']
        )

    def test_get_query_result_without_kwargs(self):
        """
        Test that retrieving the QueryResult for a query works as expected when
        executing a query
        """
        self.populate_db_with_documents(100)
        result = self.db.get_query_result(
            {'$and': [
                {'_id': {'$gte': 'julia001'}},
                {'_id': {'$lt': 'julia005'}}
            ]},
            ['_id', '_rev']
        )
        self.assertIsInstance(result, QueryResult)
        self.assertEqual(
            [doc['_id'] for doc in result],
            ['julia001', 'julia002', 'julia003', 'julia004']
        )

    def test_get_query_result_without_fields(self):
        """
        Assert that the QueryResult docs include all the expected fields when
        no fields parameter is provided.
        """
        self.populate_db_with_documents(100)
        expected_fields = ['_id', '_rev', 'age', 'name']
        # Sort the list of expected fields so we can assert list equality later
        expected_fields.sort()
        result = self.db.get_query_result(
            {'$and': [
                {'_id': {'$gte': 'julia001'}},
                {'_id': {'$lt': 'julia005'}}
            ]}
        )
        self.assertIsInstance(result, QueryResult)
        for doc in result:
            doc_fields = list(doc.keys())
            doc_fields.sort()
            self.assertEqual(doc_fields, expected_fields)
        self.assertEqual(
            [doc['_id'] for doc in result],
            ['julia001', 'julia002', 'julia003', 'julia004']
        )

    def test_get_query_result_with_empty_fields_list(self):
        """
        Assert that the QueryResult docs include all the expected fields when
        an empty fields list is provided.
        """
        self.populate_db_with_documents(100)
        expected_fields = ['_id', '_rev', 'age', 'name']
        # Sort the list of expected fields so we can assert list equality later
        expected_fields.sort()
        result = self.db.get_query_result(
            {'$and': [
                {'_id': {'$gte': 'julia001'}},
                {'_id': {'$lt': 'julia005'}}
            ]},
            fields=[]
        )
        self.assertIsInstance(result, QueryResult)
        for doc in result:
            doc_fields = list(doc.keys())
            doc_fields.sort()
            self.assertEqual(doc_fields, expected_fields)
        self.assertEqual(
            [doc['_id'] for doc in result],
            ['julia001', 'julia002', 'julia003', 'julia004']
        )

    def test_create_json_index(self):
        """
        Ensure that a JSON index is created as expected.
        """
        index = self.db.create_query_index(fields=['name', 'age'])
        self.assertIsInstance(index, Index)
        ddoc = self.db[index.design_document_id]
        self.assertTrue(ddoc['_rev'].startswith('1-'))
        self.assertEqual(ddoc,
                {'_id': index.design_document_id,
                 '_rev': ddoc['_rev'],
                 'indexes': {},
                 'lists': {},
                 'shows': {},
                 'language': 'query',
                 'views': {index.name: {'map': {'fields': {'name': 'asc',
                                                           'age': 'asc'}},
                                        'reduce': '_count',
                                        'options': {'def': {'fields': ['name',
                                                                       'age']},
                                                    }}}}
            )

    def test_create_text_index(self):
        """
        Ensure that a text index is created as expected.
        """
        index = self.db.create_query_index(
            index_type='text',
            fields=[{'name': 'name', 'type':'string'},
                    {'name': 'age', 'type':'number'}]
        )
        self.assertIsInstance(index, TextIndex)
        ddoc = self.db[index.design_document_id]
        self.assertTrue(ddoc['_rev'].startswith('1-'))
        self.assertEqual(ddoc,
                {'_id': index.design_document_id,
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'views': {},
                 'lists': {},
                 'shows': {},
                 'indexes': {index.name: {'index': {'index_array_lengths': True,
                                'fields': [{'name': 'name', 'type': 'string'},
                                           {'name': 'age', 'type': 'number'}],
                                'default_field': {},
                                'default_analyzer': 'keyword',
                                'selector': {}},
                      'analyzer': {'name': 'perfield',
                                   'default': 'keyword',
                                   'fields': {'$default': 'standard'}}}}}
            )

    def test_create_all_fields_text_index(self):
        """
        Ensure that a text index is created for all fields as expected.
        """
        index = self.db.create_query_index(index_type='text')
        self.assertIsInstance(index, TextIndex)
        ddoc = self.db[index.design_document_id]
        self.assertTrue(ddoc['_rev'].startswith('1-'))
        self.assertEqual(ddoc,
                {'_id': index.design_document_id,
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'views': {},
                 'lists': {},
                 'shows': {},
                 'indexes': {index.name: {'index': {'index_array_lengths': True,
                                'fields': 'all_fields',
                                'default_field': {},
                                'default_analyzer': 'keyword',
                                'selector': {}},
                      'analyzer': {'name': 'perfield',
                                   'default': 'keyword',
                                   'fields': {'$default': 'standard'}}}}}
            )

    def test_create_multiple_indexes_one_ddoc(self):
        """
        Tests that multiple indexes of different types can be stored in one
        design document.
        """
        json_index = self.db.create_query_index(
            'ddoc001',
            'json-index-001',
            fields=['name', 'age']
        )
        self.assertIsInstance(json_index, Index)
        search_index = self.db.create_query_index(
            'ddoc001',
            'text-index-001',
            'text',
            fields=[{'name': 'name', 'type':'string'},
                    {'name': 'age', 'type':'number'}]
        )
        self.assertIsInstance(search_index, TextIndex)
        ddoc = self.db['_design/ddoc001']
        self.assertTrue(ddoc['_rev'].startswith('2-'))
        self.assertEqual(ddoc,
                {'_id': '_design/ddoc001',
                 '_rev': ddoc['_rev'],
                 'language': 'query',
                 'lists': {},
                 'shows': {},
                 'views': {'json-index-001': {
                                'map': {'fields': {'name': 'asc',
                                                   'age': 'asc'}},
                                        'reduce': '_count',
                                        'options': {'def': {'fields': ['name',
                                                                       'age']},
                                                    }}},
                 'indexes': {'text-index-001': {
                                'index': {'index_array_lengths': True,
                                'fields': [{'name': 'name', 'type': 'string'},
                                           {'name': 'age', 'type': 'number'}],
                                'default_field': {},
                                'default_analyzer': 'keyword',
                                'selector': {}},
                      'analyzer': {'name': 'perfield',
                                   'default': 'keyword',
                                   'fields': {'$default': 'standard'}}}}}
            )

    def test_create_query_index_failure(self):
        """
        Tests that a type of something other than 'json' or 'text' will cause
        failure.
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.create_query_index(
                None,
                '_all_docs',
                'special',
                fields=[{'_id': 'asc'}]
            )
        err = cm.exception
        self.assertEqual(
            str(err),
            'Invalid index type: special.  '
            'Index type must be either \"json\" or \"text\".'
        )

    def test_delete_json_index(self):
        """
        Ensure that a JSON index is deleted as expected.
        """
        index = self.db.create_query_index(
            'ddoc001',
            'index001',
            fields=['name', 'age'])
        self.assertIsInstance(index, Index)
        ddoc = self.db['_design/ddoc001']
        self.assertTrue(ddoc.exists())
        self.db.delete_query_index('ddoc001', 'json', 'index001')
        self.assertFalse(ddoc.exists())

    def test_delete_text_index(self):
        """
        Ensure that a text index is deleted as expected.
        """
        index = self.db.create_query_index('ddoc001', 'index001', 'text')
        self.assertIsInstance(index, TextIndex)
        ddoc = self.db['_design/ddoc001']
        self.assertTrue(ddoc.exists())
        self.db.delete_query_index('ddoc001', 'text', 'index001')
        self.assertFalse(ddoc.exists())

    def test_delete_query_index_failure(self):
        """
        Tests that a type of something other than 'json' or 'text' will cause
        failure.
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.delete_query_index(None, 'special', '_all_docs')
        err = cm.exception
        self.assertEqual(
            str(err),
            'Invalid index type: special.  '
            'Index type must be either \"json\" or \"text\".'
        )

    def test_get_query_indexes_raw(self):
        """
        Tests getting all query indexes from the _index endpoint in
        JSON format.
        """
        self.db.create_query_index('ddoc001', 'json-idx-001', fields=['name', 'age'])
        self.db.create_query_index('ddoc001', 'text-idx-001', 'text')
        self.assertEqual(
            self.db.get_query_indexes(raw_result=True),
            {'indexes': [
                {'ddoc': None,
                 'name': '_all_docs',
                 'type': 'special',
                 'def': {'fields': [{'_id': 'asc'}]}},
                {'ddoc': '_design/ddoc001',
                 'name': 'json-idx-001',
                 'type': 'json',
                 'def': {'fields': [{'name': 'asc'}, {'age': 'asc'}]}},
                {'ddoc': '_design/ddoc001',
                 'name': 'text-idx-001',
                 'type': 'text',
                 'def': {'index_array_lengths': True,
                         'fields': [],
                         'default_field': {},
                         'default_analyzer': 'keyword',
                         'selector': {}}}
            ],
            'total_rows' : 3}
        )

    def test_get_query_indexes(self):
        """
        Tests getting all query indexes from the _index endpoint
        wrapped as Index, TextIndex, and SpecialIndex.
        """
        self.db.create_query_index('ddoc001', 'json-idx-001', fields=['name', 'age'])
        self.db.create_query_index('ddoc001', 'text-idx-001', 'text')
        indexes = self.db.get_query_indexes()
        self.assertIsInstance(indexes[0], SpecialIndex)
        self.assertIsNone(indexes[0].design_document_id)
        self.assertEqual(indexes[0].name, '_all_docs')
        self.assertIsInstance(indexes[1], Index)
        self.assertEqual(indexes[1].design_document_id, '_design/ddoc001')
        self.assertEqual(indexes[1].name, 'json-idx-001')
        self.assertIsInstance(indexes[2], TextIndex)
        self.assertEqual(indexes[2].design_document_id, '_design/ddoc001')
        self.assertEqual(indexes[2].name, 'text-idx-001')

    def test_get_search_result_with_invalid_argument(self):
        """
        Test get_search_result by passing in invalid arguments
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.get_search_result('searchddoc001', 'searchindex001',
                                      query='julia*', foo={'bar': 'baz'})
        err = cm.exception
        self.assertEqual(str(err), 'Invalid argument: foo')

    def test_get_search_result_with_both_q_and_query(self):
        """
        Test get_search_result by passing in both a q and query parameter
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.get_search_result('searchddoc001', 'searchindex001',
                                      query='julia*', q='julia*')
        err = cm.exception
        self.assertTrue(str(err).startswith('A single query/q parameter is required.'))

    def test_get_search_result_with_invalid_value_types(self):
        """
        Test get_search_result by passing in invalid value types for
        query parameters
        """
        test_data = [
            {'bookmark': 1},                    # Should be a STRTYPE
            {'counts': 'blah'},                 # Should be a list
            {'drilldown': 'blah'},              # Should be a list
            {'group_field': ['blah']},          # Should be a STRTYPE
            {'group_limit': 'int'},             # Should be an int
            {'group_sort': 3},                  # Should be a STRTYPE or list
            {'include_docs': 'blah'},           # Should be a boolean
            {'limit': 'blah'},                  # Should be an int
            {'ranges': 1},                      # Should be a dict
            {'sort': 10},                       # Should be a STRTYPE or list
            {'stale': ['blah']},                # Should be a STRTYPE
            {'highlight_fields': 'blah'},       # Should be a list
            {'highlight_pre_tag': ['blah']},    # Should be a STRTYPE
            {'highlight_post_tag': 1},          # Should be a STRTYPE
            {'highlight_number': ['int']},      # Should be an int
            {'highlight_size': 'blah'},         # Should be an int
            {'include_fields': 'list'},         # Should be a list
        ]

        for argument in test_data:
            with self.assertRaises(CloudantArgumentError) as cm:
                self.db.get_search_result('searchddoc001', 'searchindex001',
                                          query='julia*', **argument)
            err = cm.exception
            self.assertTrue(str(err).startswith(
                'Argument {0} is not an instance of expected type:'.format(
                    list(argument.keys())[0])
            ))

    def test_get_search_result_without_query(self):
        """
        Test get_search_result without providing a search query
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.get_search_result('searchddoc001', 'searchindex001',
                                      limit=10, include_docs=True)
        err = cm.exception
        # Validate that the error message starts as expected
        self.assertTrue(str(err).startswith('A single query/q parameter is required.'))
        # Validate that the error message includes the supplied parameters (in an order independent way)
        self.assertTrue(str(err).find("'limit': 10") >= 0)
        self.assertTrue(str(err).find("'include_docs': True") >= 0)

    def test_get_search_result_with_invalid_query_type(self):
        """
        Test get_search_result by passing an invalid query type
        """
        with self.assertRaises(CloudantArgumentError) as cm:
            self.db.get_search_result(
                'searchddoc001', 'searchindex001', query=['blah']
            )
        err = cm.exception
        self.assertTrue(str(err).startswith(
            'Argument query is not an instance of expected type:'
        ))

    def test_get_search_result_executes_search_query(self):
        """
        Test get_search_result executes a search with query parameter.
        """
        self.create_search_index()
        self.populate_db_with_documents(100)
        resp = self.db.get_search_result(
            'searchddoc001',
            'searchindex001',
            query='julia*',
            sort='_id<string>',
            limit=5,
            include_docs=True
        )
        self.assertEqual(5, len(resp['rows']))
        self.assertTrue(resp['bookmark'])

        for i, row in enumerate(resp['rows']):
            doc_id = 'julia00{0}'.format(i)

            self.assertEqual(doc_id, row['id'])
            self.assertEqual('julia', row['fields']['name'])

            # Note: The second element in the order array can be ignored. It is
            # used for troubleshooting purposes only.
            self.assertEqual(doc_id, row['order'][0])

            doc = row['doc']
            self.assertEqual(doc_id, doc['_id'])
            self.assertTrue(doc['_rev'].startswith('1-'))
            self.assertEqual(i, doc['age'])
            self.assertEqual('julia', doc['name'])

    def test_get_search_result_executes_search_q(self):
        """
        Test get_search_result executes a search query with q parameter.
        """
        self.create_search_index()
        self.populate_db_with_documents(100)
        resp = self.db.get_search_result(
            'searchddoc001',
            'searchindex001',
            q='julia*',
            sort='_id<string>',
            limit=1
        )

        self.assertTrue(resp['bookmark'])
        self.assertEqual(100, resp['total_rows'])
        self.assertEqual(1, len(resp['rows']))

        row = resp['rows'][0]
        self.assertEqual('julia000', row['id'])

        # Note: The second element in the order array can be ignored. It is
        # used for troubleshooting purposes only.
        self.assertEqual('julia000', row['order'][0])

        self.assertEqual('julia', row['fields']['name'])

    def test_get_search_result_executes_search_query_with_group_option(self):
        """
        Test get_search_result executes a search query with grouping parameters.
        """
        self.create_search_index()
        self.populate_db_with_documents(100)
        resp = self.db.get_search_result(
            'searchddoc001',
            'searchindex001',
            query='name:julia*',
            group_field='_id',
            group_limit=5,
            group_sort='_id<string>'
        )
        # for group parameter options, 'rows' results are within 'groups' key
        self.assertEqual(len(resp['groups']), 5)

        for i, group in enumerate(resp['groups']):
            by_id = 'julia00{0}'.format(i)

            self.assertEqual(by_id, group['by'])
            self.assertEqual(1, group['total_rows'])
            self.assertEqual(1, len(group['rows']))

            row = group['rows'][0]
            self.assertEqual(by_id, row['id'])
            self.assertEqual('julia', row['fields']['name'])

            # Note: The second element in the order array can be ignored. It is
            # used for troubleshooting purposes only.
            self.assertEqual(1.0, row['order'][0])

        self.assertEqual(100, resp['total_rows'])

if __name__ == '__main__':
    unittest.main()
